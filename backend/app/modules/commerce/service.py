from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.accounting.models import TaxRate
from app.modules.commerce.models import BusinessPartner, CommercePayment, PurchaseDocument, PurchaseLine, SalesDocument, SalesLine
from app.modules.inventory.items.models import InventoryItem
from app.modules.inventory.locations.models import InventoryLocation
from app.modules.inventory.stock_moves.models import InventoryStockMove
from app.modules.inventory.stock_moves.schemas import StockMoveCreate
from app.modules.inventory.stock_moves.service import inventory_stock_move_service

SALE_TYPES = {"quotation", "order", "delivery", "invoice", "credit_note"}
PURCHASE_TYPES = {"requisition", "rfq", "order", "receipt", "bill", "debit_note"}


class CommerceService:
    def create_partner(self, db: Session, payload):
        if db.scalar(select(BusinessPartner).where(BusinessPartner.company_id == payload.company_id, BusinessPartner.code == payload.code)):
            raise ValueError("Partner code already exists")
        obj = BusinessPartner(**payload.model_dump())
        db.add(obj); db.flush(); return obj

    def list_partners(self, db, company_id, partner_type=None):
        q = select(BusinessPartner).where(BusinessPartner.company_id == company_id, BusinessPartner.is_active.is_(True))
        if partner_type: q = q.where(BusinessPartner.partner_type.in_([partner_type, "both"]))
        return list(db.scalars(q.order_by(BusinessPartner.name)).all())

    def create_document(self, db: Session, payload):
        is_sale = payload.document_type in SALE_TYPES
        if not is_sale and payload.document_type not in PURCHASE_TYPES: raise ValueError("Unsupported document type")
        partner = db.scalar(select(BusinessPartner).where(BusinessPartner.id == payload.partner_id, BusinessPartner.company_id == payload.company_id, BusinessPartner.is_active.is_(True)))
        if not partner: raise ValueError("Partner not found")
        if is_sale and partner.partner_type not in ("customer", "both"): raise ValueError("Partner is not a customer")
        if not is_sale and partner.partner_type not in ("vendor", "both"): raise ValueError("Partner is not a vendor")
        model = SalesDocument if is_sale else PurchaseDocument
        line_model = SalesLine if is_sale else PurchaseLine
        if db.scalar(select(model).where(model.company_id == payload.company_id, model.number == payload.number)): raise ValueError("Document number already exists")
        obj = model(company_id=payload.company_id, partner_id=payload.partner_id, document_type=payload.document_type, number=payload.number, document_date=payload.document_date, warehouse_id=payload.warehouse_id, notes=payload.notes)
        subtotal = Decimal("0"); tax = Decimal("0"); discount = Decimal("0")
        for p in payload.lines:
            item = db.scalar(select(InventoryItem).where(InventoryItem.id == p.item_id, InventoryItem.company_id == payload.company_id, InventoryItem.is_active.is_(True)))
            if not item: raise ValueError(f"Item {p.item_id} not found")
            tax_percent = Decimal(p.tax_percent)
            if p.tax_rate_id:
                tax_rate = db.scalar(select(TaxRate).where(TaxRate.id == p.tax_rate_id, TaxRate.company_id == payload.company_id, TaxRate.is_active.is_(True)))
                if not tax_rate: raise ValueError(f"Tax rate {p.tax_rate_id} not found")
                tax_percent = Decimal(tax_rate.rate)
                if tax_rate.is_withholding: raise ValueError("Withholding tax must be applied at payment, not as invoice VAT")
            gross = p.quantity * p.unit_price; disc = gross * p.discount_percent / Decimal("100"); net = gross - disc; tx = net * tax_percent / Decimal("100")
            obj.lines.append(line_model(item_id=p.item_id, tax_rate_id=p.tax_rate_id, description=p.description, quantity=p.quantity, unit_price=p.unit_price, discount_percent=p.discount_percent, tax_percent=tax_percent, line_total=net + tx))
            subtotal += net; discount += disc; tax += tx
        obj.subtotal = subtotal; obj.discount_total = discount; obj.tax_total = tax; obj.total = subtotal + tax
        db.add(obj); db.flush(); return obj

    def list_documents(self, db, company_id, kind):
        model = SalesDocument if kind == "sale" else PurchaseDocument
        return list(db.scalars(select(model).where(model.company_id == company_id).order_by(model.document_date.desc(), model.id.desc())).all())

    def confirm(self, db, company_id, document_id, kind):
        model = SalesDocument if kind == "sale" else PurchaseDocument
        obj = db.scalar(select(model).where(model.id == document_id, model.company_id == company_id).with_for_update())
        if not obj: raise ValueError("Document not found")
        if obj.status != "draft": raise ValueError("Only draft documents can be confirmed")
        obj.status = "confirmed"; db.flush(); return obj

    def post_inventory(self, db, company_id, document_id, kind):
        model = SalesDocument if kind == "sale" else PurchaseDocument
        obj = db.scalar(select(model).where(model.id == document_id, model.company_id == company_id).with_for_update())
        if not obj: raise ValueError("Document not found")
        allowed = {"delivery"} if kind == "sale" else {"receipt"}
        if obj.document_type not in allowed: raise ValueError("Only delivery documents and purchase receipts post inventory; invoices/bills are accounting documents")
        if obj.status not in ("confirmed", "partially_fulfilled"):
            if obj.status in ("fulfilled", "received"): return obj
            raise ValueError("Document must be confirmed before inventory posting")
        if not obj.warehouse_id: raise ValueError("Warehouse is required")
        locations = list(db.scalars(select(InventoryLocation).where(InventoryLocation.warehouse_id == obj.warehouse_id, InventoryLocation.company_id == company_id, InventoryLocation.is_active.is_(True)).order_by(InventoryLocation.id)).all())
        if not locations: raise ValueError("Warehouse has no active location")
        loc = locations[0]; source_entity = "sales_delivery" if kind == "sale" else "purchase_receipt"
        for line in obj.lines:
            source_id = f"{obj.id}:{line.id}"
            existing = db.scalar(select(InventoryStockMove).where(InventoryStockMove.company_id == company_id, InventoryStockMove.source_module == "commerce", InventoryStockMove.source_entity == source_entity, InventoryStockMove.source_id == source_id, InventoryStockMove.status.in_(["draft", "posted"])))
            if existing: continue
            if kind == "sale":
                payload = StockMoveCreate(company_id=company_id, item_id=line.item_id, movement_type="issue", source_location_id=loc.id, destination_location_id=None, quantity=line.quantity, unit_cost=0, reference=obj.number, notes="Sales delivery")
            else:
                payload = StockMoveCreate(company_id=company_id, item_id=line.item_id, movement_type="receipt", source_location_id=None, destination_location_id=loc.id, quantity=line.quantity, unit_cost=line.unit_price, reference=obj.number, notes="Purchase receipt")
            move = inventory_stock_move_service.create_draft(db, payload); move.source_module = "commerce"; move.source_entity = source_entity; move.source_id = source_id
            inventory_stock_move_service.post(db, company_id=company_id, move_id=move.id)
        obj.status = "fulfilled" if kind == "sale" else "received"; db.flush(); return obj

    def pay(self, db, payload, kind):
        model = SalesDocument if kind == "sale" else PurchaseDocument
        obj = db.scalar(select(model).where(model.id == payload.document_id, model.company_id == payload.company_id).with_for_update())
        if not obj: raise ValueError("Document not found")
        balance = Decimal(obj.total or 0) - Decimal(obj.paid_total or 0)
        if payload.amount > balance: raise ValueError("Payment exceeds outstanding balance")
        payment = CommercePayment(document_kind=kind, **payload.model_dump())
        db.add(payment); obj.paid_total = Decimal(obj.paid_total or 0) + payload.amount; db.flush()
        return obj, payment

    def reverse_payment(self, db, company_id: int, payment_id: int, reversal_date, notes=None):
        payment = db.scalar(select(CommercePayment).where(CommercePayment.id == payment_id, CommercePayment.company_id == company_id).with_for_update())
        if not payment: raise ValueError("Payment not found")
        if payment.status == "reversed": raise ValueError("Payment is already reversed")
        if payment.reversed_of_id: raise ValueError("This payment is a reversal entry and cannot be reversed")
        model = SalesDocument if payment.document_kind == "sale" else PurchaseDocument
        document = db.scalar(select(model).where(model.id == payment.document_id, model.company_id == company_id).with_for_update())
        if not document: raise ValueError("Document not found")
        if Decimal(document.paid_total or 0) < Decimal(payment.amount): raise ValueError("Document paid total is inconsistent with the payment")
        payment.status = "reversed"; payment.reversed_at = reversal_date
        reversal = CommercePayment(company_id=company_id, document_kind=payment.document_kind, document_id=payment.document_id, payment_date=reversal_date, amount=payment.amount, wht_amount=payment.wht_amount, method=payment.method, reference=f"REV-{payment.id}", notes=notes or f"Reversal of payment {payment.id}", status="reversed", reversed_of_id=payment.id, reversed_at=reversal_date)
        db.add(reversal); document.paid_total = Decimal(document.paid_total or 0) - Decimal(payment.amount); db.flush()
        return document, payment, reversal


commerce_service = CommerceService()
