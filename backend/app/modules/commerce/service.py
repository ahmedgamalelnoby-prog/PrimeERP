from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.accounting.models import TaxRate
from app.modules.companies.models import Company
from app.modules.identity.models import User
from app.modules.accounting.tax_engine import calculate_taxes
from app.modules.commerce.accounting_service import commerce_accounting_service
from app.modules.catalog.models import ProductVariant
from app.modules.commerce.models import BusinessPartner, CommercePayment, CommercePaymentAllocation, PurchaseBillReceiptLink, PurchaseDocument, PurchaseLine, SalesDocument, SalesLine
from app.modules.commerce.payment_workflow import post_payment, reverse_payment
from app.modules.inventory.items.models import InventoryItem
from app.modules.inventory.locations.models import InventoryLocation
from app.modules.inventory.stock_moves.models import InventoryStockMove
from app.modules.inventory.stock_moves.schemas import StockMoveCreate
from app.modules.inventory.stock_moves.service import inventory_stock_move_service
from app.modules.inventory.warehouses.models import InventoryWarehouse
from app.modules.treasury.models import Cheque, ChequeEvent

SALE_TYPES = {"quotation", "order", "delivery", "invoice", "credit_note"}
PURCHASE_TYPES = {"requisition", "rfq", "order", "receipt", "bill", "debit_note"}

def resolve_due_date(document_type: str, document_date, explicit_due_date, payment_terms_days: int):
    if explicit_due_date is not None:
        if explicit_due_date < document_date:
            raise ValueError("Due date cannot be earlier than document date")
        return explicit_due_date
    if document_type in {"invoice", "bill"}:
        return document_date + timedelta(days=payment_terms_days)
    return None

class CommerceService:
    def create_partner(self, db: Session, payload):
        if db.scalar(select(BusinessPartner).where(BusinessPartner.company_id == payload.company_id, BusinessPartner.code == payload.code)): raise ValueError("Partner code already exists")
        obj = BusinessPartner(**payload.model_dump()); db.add(obj); db.flush(); return obj

    def list_partners(self, db, company_id, partner_type=None):
        q = select(BusinessPartner).where(BusinessPartner.company_id == company_id, BusinessPartner.is_active.is_(True))
        if partner_type: q = q.where(BusinessPartner.partner_type.in_([partner_type, "both"]))
        return list(db.scalars(q.order_by(BusinessPartner.name)).all())

    def _resolve_line_variant(self, db: Session, *, company_id: int, item: InventoryItem, variant_id: int | None):
        active_variants = db.scalar(select(ProductVariant.id).where(ProductVariant.company_id == company_id, ProductVariant.product_id == item.id, ProductVariant.is_active.is_(True)).limit(1))
        if variant_id is None:
            if active_variants is not None: raise ValueError("This item has active variants; document lines must identify the variant")
            return None
        variant = db.scalar(select(ProductVariant).where(ProductVariant.id == variant_id, ProductVariant.company_id == company_id, ProductVariant.product_id == item.id, ProductVariant.is_active.is_(True)))
        if variant is None: raise ValueError("Variant does not belong to the item/company or is inactive")
        return variant

    def _resolve_line_tax_ids(self, db: Session, *, company_id: int, item: InventoryItem, explicit_tax_ids: list[int] | None, is_sale: bool) -> list[int]:
        tax_ids = list(explicit_tax_ids) if explicit_tax_ids is not None else list((item.sales_tax_ids if is_sale else item.purchase_tax_ids) or [])
        if not tax_ids: return []
        taxes = list(db.scalars(select(TaxRate).where(TaxRate.company_id == company_id, TaxRate.id.in_(tax_ids), TaxRate.is_active.is_(True))).all()); found = {tax.id for tax in taxes}; missing = [tax_id for tax_id in tax_ids if tax_id not in found]
        if missing: raise ValueError(f"Tax rate(s) not found or inactive: {missing}")
        return tax_ids

    def _document_wht_total(self, db: Session, *, document, company_id: int) -> Decimal:
        total = Decimal("0")
        for line in document.lines:
            tax_ids = list(getattr(line, "tax_rate_ids", None) or [])
            if not tax_ids and getattr(line, "tax_rate_id", None): tax_ids = [line.tax_rate_id]
            if not tax_ids: continue
            taxes = list(db.scalars(select(TaxRate).where(TaxRate.company_id == company_id, TaxRate.id.in_(tax_ids), TaxRate.is_active.is_(True))).all())
            gross = Decimal(line.quantity) * Decimal(line.unit_price); net = gross - gross * Decimal(line.discount_percent or 0) / Decimal("100")
            for rate in [Decimal(tax.rate) for tax in taxes if tax.is_withholding]: total += net * rate / Decimal("100")
        return total.quantize(Decimal("0.01"))

    def _auto_payment_wht(self, db: Session, *, document, company_id: int, amount: Decimal, document_kind: str) -> Decimal:
        document_wht = self._document_wht_total(db, document=document, company_id=company_id)
        if document_wht <= 0: return Decimal("0")
        paid_wht = sum((Decimal(p.wht_amount or 0) for p in db.scalars(select(CommercePayment).where(CommercePayment.company_id == company_id, CommercePayment.document_kind == document_kind, CommercePayment.document_id == document.id, CommercePayment.status == "posted")).all()), Decimal("0"))
        remaining_wht = max(document_wht - paid_wht, Decimal("0")); outstanding = Decimal(document.total or 0) - Decimal(document.paid_total or 0)
        if remaining_wht <= 0 or outstanding <= 0: return Decimal("0")
        return min(remaining_wht, (remaining_wht * amount / outstanding).quantize(Decimal("0.01")))

    def create_document(self, db, payload):
        is_sale = payload.document_type in SALE_TYPES
        if not is_sale and payload.document_type not in PURCHASE_TYPES: raise ValueError("Unsupported document type")
        partner = db.scalar(select(BusinessPartner).where(BusinessPartner.id == payload.partner_id, BusinessPartner.company_id == payload.company_id, BusinessPartner.is_active.is_(True)))
        if not partner: raise ValueError("Partner not found")
        if is_sale and partner.partner_type not in ("customer", "both"): raise ValueError("Partner is not a customer")
        if not is_sale and partner.partner_type not in ("vendor", "both"): raise ValueError("Partner is not a vendor")
        if payload.warehouse_id is not None and db.scalar(select(InventoryWarehouse).where(InventoryWarehouse.id == payload.warehouse_id, InventoryWarehouse.company_id == payload.company_id, InventoryWarehouse.is_active.is_(True))) is None: raise ValueError("Warehouse does not belong to the company or is inactive")
        model = SalesDocument if is_sale else PurchaseDocument; line_model = SalesLine if is_sale else PurchaseLine
        if db.scalar(select(model).where(model.company_id == payload.company_id, model.number == payload.number)): raise ValueError("Document number already exists")
        if payload.receipt_ids:
            receipts = list(db.scalars(select(PurchaseDocument).where(PurchaseDocument.id.in_(payload.receipt_ids), PurchaseDocument.company_id == payload.company_id, PurchaseDocument.partner_id == payload.partner_id, PurchaseDocument.document_type == "receipt", PurchaseDocument.status.in_(["received", "partially_received"]))).all()); found = {r.id for r in receipts}; missing = [r for r in payload.receipt_ids if r not in found]
            if missing: raise ValueError(f"Receipt(s) not found, not received, or not owned by the vendor/company: {missing}")
        obj = model(company_id=payload.company_id, partner_id=payload.partner_id, document_type=payload.document_type, number=payload.number, document_date=payload.document_date, warehouse_id=payload.warehouse_id, due_date=resolve_due_date(payload.document_type, payload.document_date, payload.due_date, partner.payment_terms_days), notes=payload.notes)
        subtotal = Decimal("0"); tax = Decimal("0"); discount = Decimal("0")
        for p in payload.lines:
            item = db.scalar(select(InventoryItem).where(InventoryItem.id == p.item_id, InventoryItem.company_id == payload.company_id, InventoryItem.is_active.is_(True)))
            if not item: raise ValueError(f"Item {p.item_id} not found")
            variant_id = getattr(p, "variant_id", None); self._resolve_line_variant(db, company_id=payload.company_id, item=item, variant_id=variant_id)
            explicit_tax_ids = getattr(p, "tax_rate_ids", None); tax_ids = self._resolve_line_tax_ids(db, company_id=payload.company_id, item=item, explicit_tax_ids=explicit_tax_ids, is_sale=is_sale)
            if explicit_tax_ids is None and p.tax_percent != 0: raise ValueError("Tax Master is required for non-zero tax rates")
            gross = p.quantity * p.unit_price; disc = gross * p.discount_percent / Decimal("100"); net = gross - disc
            if net < 0: raise ValueError("Line discount cannot exceed the line gross amount")
            tax_result = calculate_taxes(db, company_id=payload.company_id, amount=net, tax_ids=tax_ids, inclusive=False); tax_amount = Decimal(tax_result["tax_total"]); line_total = net + tax_amount
            tax_rows = list(db.scalars(select(TaxRate).where(TaxRate.id.in_(tax_ids), TaxRate.company_id == payload.company_id)).all()) if tax_ids else []
            non_wht_ids = [tax.id for tax in tax_rows if not tax.is_withholding]; primary_tax_id = non_wht_ids[0] if non_wht_ids else (tax_ids[0] if tax_ids else None); primary_tax_percent = Decimal(next((tax.rate for tax in tax_rows if tax.id == primary_tax_id), 0))
            obj.lines.append(line_model(item_id=p.item_id, variant_id=variant_id, tax_rate_id=primary_tax_id, tax_rate_ids=tax_ids, description=p.description, quantity=p.quantity, unit_price=p.unit_price, discount_percent=p.discount_percent, tax_percent=primary_tax_percent, line_total=line_total)); subtotal += net; discount += disc; tax += tax_amount
        obj.subtotal = subtotal; obj.discount_total = discount; obj.tax_total = tax; obj.total = subtotal + tax; db.add(obj); db.flush()
        if payload.receipt_ids:
            for receipt_id in payload.receipt_ids: db.add(PurchaseBillReceiptLink(company_id=payload.company_id, bill_id=obj.id, receipt_id=receipt_id))
            db.flush()
        return obj

    def list_documents(self, db, company_id, kind):
        model = SalesDocument if kind == "sale" else PurchaseDocument
        return list(db.scalars(select(model).where(model.company_id == company_id).order_by(model.document_date.desc(), model.id.desc())).all())

    def partner_open_balance(self, db, company_id: int, partner_id: int, direction: str, *, before_date=None):
        model = SalesDocument if direction == "customer" else PurchaseDocument
        positive_type = "invoice" if direction == "customer" else "bill"
        offset_type = "credit_note" if direction == "customer" else "debit_note"
        q = select(model).where(model.company_id == company_id, model.partner_id == partner_id, model.status.in_({"confirmed", "posted"}), model.document_type.in_({positive_type, offset_type}))
        if before_date is not None:
            q = q.where(model.document_date < before_date)
        total = Decimal("0")
        for doc in db.scalars(q).all():
            value = Decimal(doc.total or 0)
            total += value if doc.document_type == positive_type else -value
            if doc.document_type == positive_type:
                total -= Decimal(doc.paid_total or 0)
        return total

    def enforce_credit_limit(self, db, company_id: int, document):
        if document.document_type != "invoice":
            return
        partner = db.scalar(select(BusinessPartner).where(BusinessPartner.id == document.partner_id, BusinessPartner.company_id == company_id).with_for_update())
        limit = Decimal(partner.credit_limit or 0) if partner else Decimal("0")
        if limit <= 0:
            return
        existing = self.partner_open_balance(db, company_id, document.partner_id, "customer", before_date=None)
        exposure = existing + Decimal(document.total or 0)
        if exposure > limit:
            raise ValueError(f"Customer credit limit exceeded: exposure {exposure} is above limit {limit}")

    def confirm(self, db, company_id, document_id, kind, user_id: int | None = None):
        model = SalesDocument if kind == "sale" else PurchaseDocument; obj = db.scalar(select(model).where(model.id == document_id, model.company_id == company_id).with_for_update())
        if not obj: raise ValueError("Document not found")
        if obj.status != "draft": raise ValueError("Only draft documents can be confirmed")
        if not obj.lines: raise ValueError("A document must contain at least one line before confirmation")
        if kind == "sale":
            self.enforce_credit_limit(db, company_id, obj)
        obj.status = "confirmed"; db.flush()
        if user_id is not None:
            if kind == "sale":
                if obj.document_type == "invoice": commerce_accounting_service.post_sales_invoice(db, obj, user_id)
                elif obj.document_type == "credit_note": commerce_accounting_service.post_sales_credit_note(db, obj, user_id)
            if kind == "purchase":
                if obj.document_type == "bill": commerce_accounting_service.post_purchase_bill(db, obj, user_id)
                elif obj.document_type == "debit_note": commerce_accounting_service.post_purchase_debit_note(db, obj, user_id)
        return obj

    def post_inventory(self, db, company_id, document_id, kind, user_id: int | None = None):
        model = SalesDocument if kind == "sale" else PurchaseDocument; obj = db.scalar(select(model).where(model.id == document_id, model.company_id == company_id).with_for_update())
        if not obj: raise ValueError("Document not found")
        allowed = {"delivery"} if kind == "sale" else {"receipt"}
        if obj.document_type not in allowed: raise ValueError("Only delivery documents and purchase receipts post inventory; invoices/bills are accounting documents")
        if obj.status not in ("confirmed", "partially_fulfilled"):
            if obj.status in ("fulfilled", "received"): return obj
            raise ValueError("Document must be confirmed before inventory posting")
        if not obj.warehouse_id: raise ValueError("Warehouse is required")
        company = db.scalar(select(Company).where(Company.id == company_id))
        if company is None or company.tenant_id is None:
            raise ValueError("Company tenant context is missing")
        tenant_id = company.tenant_id
        if user_id is None:
            user = db.scalar(select(User).where(User.tenant_id == tenant_id, User.is_active.is_(True)).order_by(User.id))
            if user is None:
                raise ValueError("No active tenant user is available for inventory posting")
            user_id = user.id
        locations = list(db.scalars(select(InventoryLocation).where(InventoryLocation.warehouse_id == obj.warehouse_id, InventoryLocation.company_id == company_id, InventoryLocation.is_active.is_(True)).order_by(InventoryLocation.id)).all())
        if not locations: raise ValueError("Warehouse has no active location")
        loc = locations[0]; source_entity = "sales_delivery" if kind == "sale" else "purchase_receipt"
        for line in obj.lines:
            source_id = f"{obj.id}:{line.id}"
            existing = db.scalar(select(InventoryStockMove).where(InventoryStockMove.company_id == company_id, InventoryStockMove.source_module == "commerce", InventoryStockMove.source_entity == source_entity, InventoryStockMove.source_id == source_id, InventoryStockMove.status.in_(["draft", "posted"])))
            if existing: continue
            if kind == "sale": payload = StockMoveCreate(company_id=company_id, item_id=line.item_id, variant_id=line.variant_id, movement_type="issue", source_location_id=loc.id, destination_location_id=None, quantity=line.quantity, unit_cost=0, transaction_date=obj.document_date, reference=obj.number, source_module="commerce", source_entity=source_entity, source_id=source_id, notes="Sales delivery")
            else:
                net_unit_cost = Decimal(line.unit_price) * (Decimal("100") - Decimal(line.discount_percent or 0)) / Decimal("100")
                payload = StockMoveCreate(company_id=company_id, item_id=line.item_id, variant_id=getattr(line, "variant_id", None), movement_type="receipt", source_location_id=None, destination_location_id=loc.id, quantity=line.quantity, unit_cost=net_unit_cost, transaction_date=obj.document_date, reference=obj.number, source_module="commerce", source_entity=source_entity, source_id=source_id, notes="Purchase receipt")
            move = inventory_stock_move_service.create_draft(db, payload)
            inventory_stock_move_service.post(db, tenant_id=tenant_id, company_id=company_id, move_id=move.id, user_id=user_id)
        if kind == "sale":
            commerce_accounting_service.post_sales_delivery_cogs(db, obj, user_id)
        else:
            commerce_accounting_service.post_purchase_receipt(db, obj, user_id)
        obj.status = "fulfilled" if kind == "sale" else "received"; db.flush()
        return obj

    @staticmethod
    def _payment_value(payment, key):
        if isinstance(payment, dict):
            return payment.get(key)
        return getattr(payment, key, None)

    def _ensure_payment_allocation(self, db, payment, document, allocations=None):
        company_id = self._payment_value(payment, "company_id")
        payment_id = self._payment_value(payment, "id")
        document_kind = self._payment_value(payment, "document_kind")
        amount = Decimal(self._payment_value(payment, "amount") or 0)
        if company_id is None or payment_id is None or document_kind is None or amount <= 0:
            raise ValueError("Payment result is missing allocation identity fields")
        targets = allocations or [{"document_id": document.id, "amount": amount}]
        allocation_total = sum((Decimal(a["amount"]) for a in targets), Decimal("0"))
        if allocation_total > amount:
            raise ValueError("Payment allocations cannot exceed payment amount")
        model = SalesDocument if document_kind == "sale" else PurchaseDocument
        positive_type = "invoice" if document_kind == "sale" else "bill"
        payment_partner = db.scalar(select(model.partner_id).where(model.id == document.id, model.company_id == company_id))
        if payment_partner is None:
            raise ValueError("Payment source document not found")
        created = []
        for target in targets:
            target_id = int(target["document_id"])
            target_amount = Decimal(target["amount"])
            target_doc = db.scalar(select(model).where(
                model.id == target_id,
                model.company_id == company_id,
                model.partner_id == payment_partner,
                model.document_type == positive_type,
                model.status.in_({"confirmed", "posted"}),
            ).with_for_update())
            if target_doc is None:
                raise ValueError("Payment allocation document must be an open invoice/bill for the same partner")
            outstanding = Decimal(target_doc.total or 0) - Decimal(target_doc.paid_total or 0)
            if target_amount > outstanding:
                raise ValueError("Payment allocation exceeds document outstanding balance")
            existing = db.scalar(select(CommercePaymentAllocation).where(
                CommercePaymentAllocation.company_id == company_id,
                CommercePaymentAllocation.payment_id == payment_id,
                CommercePaymentAllocation.document_kind == document_kind,
                CommercePaymentAllocation.document_id == target_id,
            ).with_for_update())
            if existing is None:
                existing = CommercePaymentAllocation(
                    company_id=company_id,
                    payment_id=payment_id,
                    document_kind=document_kind,
                    document_id=target_id,
                    amount=target_amount,
                    status="active",
                )
                db.add(existing)
            elif existing.status != "active" or Decimal(existing.amount) != target_amount:
                raise ValueError("Payment allocation already exists with a different amount")
            else:
                created.append(existing)
                continue
            target_doc.paid_total = Decimal(target_doc.paid_total or 0) + target_amount
            created.append(existing)
        db.flush()
        return created

    def pay(self, db, payload, kind, user_id: int | None = None):
        model = SalesDocument if kind == "sale" else PurchaseDocument; allowed_types = {"invoice"} if kind == "sale" else {"bill"}
        document = db.scalar(select(model).where(model.id == payload.document_id, model.company_id == payload.company_id).with_for_update())
        if document is None: raise ValueError("Document not found")
        document_type = getattr(document, "document_type", "invoice" if kind == "sale" else "bill")
        document_status = getattr(document, "status", "confirmed")
        if document_type not in allowed_types: raise ValueError("Payments are allowed only for invoices and bills")
        if document_status not in {"confirmed", "posted"}: raise ValueError("Document must be confirmed or posted before payment")
        wht_amount = Decimal(payload.wht_amount or 0)
        if wht_amount == 0 and getattr(payload, "auto_wht", True): wht_amount = self._auto_payment_wht(db, document=document, company_id=payload.company_id, amount=Decimal(payload.amount), document_kind=kind)
        payment_result = post_payment(db, company_id=payload.company_id, document_kind=kind, document_id=payload.document_id, amount=payload.amount, payment_date=payload.payment_date, method=payload.method, wht_amount=wht_amount, reference=payload.reference, notes=payload.notes, idempotency_key=payload.idempotency_key, update_document_paid_total=not bool(getattr(payload, "allocations", None)))
        if isinstance(payment_result, tuple) and len(payment_result) == 2:
            document, payment = payment_result
        else:
            payment = payment_result
        allocations = getattr(payload, "allocations", None) or None
        self._ensure_payment_allocation(db, payment, document, [a.model_dump() for a in allocations] if allocations else None)
        if payload.method.lower() == "cheque":
            # Payment idempotency can return the already-posted payment on a
            # retry. The cheque is a side effect of that payment, so it must
            # be created exactly once as well.
            existing_cheque = db.scalar(
                select(Cheque).where(
                    Cheque.company_id == payload.company_id,
                    Cheque.source_payment_id == payment.id,
                ).with_for_update()
            )
            if existing_cheque is None:
                if not payload.cheque_number:
                    raise ValueError("Cheque number is required for cheque payments")
                due_date = payload.cheque_due_date or payload.payment_date
                if due_date < payload.payment_date:
                    raise ValueError("Cheque due date cannot be earlier than payment date")
                direction = "received" if kind == "sale" else "issued"
                now = datetime.now(timezone.utc)
                cheque = Cheque(
                    company_id=payload.company_id,
                    partner_id=document.partner_id,
                    direction=direction,
                    cheque_number=payload.cheque_number,
                    bank_name=payload.cheque_bank_name,
                    account_number=payload.cheque_account_number,
                    cheque_date=payload.payment_date,
                    due_date=due_date,
                    amount=payload.amount,
                    currency="EGP",
                    status=direction,
                    source_payment_id=payment.id,
                    notes=payload.notes,
                    created_at=now,
                    updated_at=now,
                )
                db.add(cheque)
                db.flush()
                db.add(ChequeEvent(
                    company_id=payload.company_id,
                    cheque_id=cheque.id,
                    event_type="created_from_payment",
                    from_status=None,
                    to_status=direction,
                    event_date=payload.payment_date,
                    reference=payload.reference,
                    notes=payload.notes,
                    created_by=user_id,
                    created_at=now,
                ))
        if user_id is not None: commerce_accounting_service.post_payment(db, payment, document, user_id)
        return document, payment

    def reverse_payment(self, db, company_id: int, payment_id: int, reversal_date, notes=None, user_id: int | None = None):
        document, payment, reversal = reverse_payment(db, company_id=company_id, payment_id=payment_id, reversal_date=reversal_date, notes=notes)
        if user_id is not None: commerce_accounting_service.post_payment_reversal(db, payment, document, user_id, reversal_date=reversal_date)
        return document, payment, reversal


    def ar_ap_aging(self, db, company_id: int, as_of):
        rows = []
        for model, direction in ((SalesDocument, "receivable"), (PurchaseDocument, "payable")):
            positive_type = "invoice" if direction == "receivable" else "bill"
            offset_type = "credit_note" if direction == "receivable" else "debit_note"
            documents = db.scalars(select(model).where(
                model.company_id == company_id,
                model.document_type == positive_type,
                model.status.in_({"confirmed", "posted"}),
                model.total > model.paid_total,
            ).order_by(model.due_date, model.id)).all()
            offsets = {}
            for note in db.scalars(select(model).where(
                model.company_id == company_id,
                model.document_type == offset_type,
                model.status.in_({"confirmed", "posted"}),
            )).all():
                offsets[note.partner_id] = offsets.get(note.partner_id, Decimal("0")) + Decimal(note.total or 0)
            for document in documents:
                outstanding = Decimal(document.total or 0) - Decimal(document.paid_total or 0)
                partner_offset = offsets.get(document.partner_id, Decimal("0"))
                if partner_offset > 0:
                    applied = min(outstanding, partner_offset)
                    outstanding -= applied
                    offsets[document.partner_id] = partner_offset - applied
                if outstanding <= 0:
                    continue
                due_date = document.due_date or document.document_date
                days_overdue = max((as_of - due_date).days, 0)
                bucket = "current" if days_overdue == 0 else "1-30" if days_overdue <= 30 else "31-60" if days_overdue <= 60 else "61-90" if days_overdue <= 90 else "91+"
                rows.append({
                    "direction": direction, "document_id": document.id, "document_number": document.number,
                    "partner_id": document.partner_id, "document_date": document.document_date, "due_date": due_date,
                    "total": document.total, "paid_total": Decimal(document.total or 0) - outstanding, "outstanding": outstanding,
                    "days_overdue": days_overdue, "bucket": bucket,
                })
        return rows

    def partner_statement(self, db, company_id: int, partner_id: int, direction: str, from_date=None, to_date=None, as_of=None):
        if direction not in {"customer", "vendor"}:
            raise ValueError("Invalid statement direction")
        model = SalesDocument if direction == "customer" else PurchaseDocument
        positive_type = "invoice" if direction == "customer" else "bill"
        offset_type = "credit_note" if direction == "customer" else "debit_note"
        cutoff = as_of or to_date
        if cutoff is None:
            from datetime import date
            cutoff = date.today()
        partner = db.scalar(select(BusinessPartner).where(BusinessPartner.id == partner_id, BusinessPartner.company_id == company_id, BusinessPartner.is_active.is_(True)))
        if partner is None:
            raise ValueError("Partner not found")
        docs = list(db.scalars(select(model).where(
            model.company_id == company_id, model.partner_id == partner_id,
            model.document_type.in_({positive_type, offset_type}),
            model.status.in_({"confirmed", "posted"}),
            model.document_date <= cutoff,
        ).order_by(model.document_date, model.id)).all())
        payments = list(db.scalars(select(CommercePayment).where(
            CommercePayment.company_id == company_id,
            CommercePayment.document_kind == ("sale" if direction == "customer" else "purchase"),
            CommercePayment.document_id.in_([d.id for d in docs] or [-1]),
            CommercePayment.status == "posted",
            CommercePayment.payment_date <= cutoff,
        ).order_by(CommercePayment.payment_date, CommercePayment.id)).all())
        events = []
        for doc in docs:
            is_positive = doc.document_type == positive_type
            events.append((doc.document_date, doc.id, doc.document_type, doc.number, Decimal(doc.total or 0) if is_positive else -Decimal(doc.total or 0), 0))
        for payment in payments:
            events.append((payment.payment_date, 10_000_000 + payment.id, "payment", f"PAY-{payment.id}", 0, Decimal(payment.amount)))
        events.sort(key=lambda x: (x[0], x[1]))
        balance = Decimal("0")
        opening = Decimal("0")
        rows = []
        for event_date, _, event_type, reference, debit_base, credit_base in events:
            movement = debit_base - credit_base
            if from_date is not None and event_date < from_date:
                balance += movement
                opening = balance
                continue
            balance += movement
            rows.append({"date": event_date, "document_type": event_type, "document_id": None if event_type == "payment" else int(reference.split("-")[-1]) if reference.split("-")[-1].isdigit() else None, "reference": reference, "debit": debit_base, "credit": credit_base, "balance": balance})
        return {"opening_balance": opening, "closing_balance": balance, "rows": rows}


commerce_service = CommerceService()
