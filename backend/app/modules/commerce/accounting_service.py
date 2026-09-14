from datetime import date
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.accounting.compliance_controls import validate_double_entry, validate_source
from app.modules.accounting.fiscal_years.models import AccountingPeriod, FiscalYear
from app.modules.accounting.journals.models import AccountingJournal, JournalEntry
from app.modules.accounting.journals.services.journal_service import journal_service
from app.modules.commerce.accounting_models import CommerceAccountingSettings
from app.modules.commerce.models import PurchaseBillReceiptAllocation, PurchaseBillReceiptLink
from app.modules.companies.models import Company
from app.modules.branches.models import Branch
from app.modules.inventory.items.models import InventoryItem
from app.modules.inventory.stock_moves.models import InventoryStockMove


class CommerceAccountingService:
    def _settings(self, db: Session, company_id: int) -> CommerceAccountingSettings:
        obj = db.scalar(select(CommerceAccountingSettings).where(CommerceAccountingSettings.company_id == company_id))
        if obj is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Commerce accounting configuration is missing for this company")
        return obj

    def _context(self, db: Session, company_id: int, entry_date: date):
        settings = self._settings(db, company_id)
        company = db.scalar(select(Company).where(Company.id == company_id))
        if company is None:
            raise HTTPException(404, "Company not found")
        branch = db.scalar(select(Branch).where(Branch.id == settings.default_branch_id, Branch.company_id == company_id, Branch.tenant_id == company.tenant_id, Branch.is_active.is_(True)))
        if branch is None:
            raise HTTPException(409, "Configured accounting branch was not found")
        period = db.scalar(select(AccountingPeriod).where(AccountingPeriod.company_id == company_id, AccountingPeriod.tenant_id == company.tenant_id, AccountingPeriod.start_date <= entry_date, AccountingPeriod.end_date >= entry_date, AccountingPeriod.status == "open", AccountingPeriod.allow_posting.is_(True)).order_by(AccountingPeriod.period_number.desc()))
        if period is None:
            raise HTTPException(409, "No open posting period exists for the document date")
        fiscal_year = db.scalar(select(FiscalYear).where(FiscalYear.id == period.fiscal_year_id, FiscalYear.company_id == company_id, FiscalYear.tenant_id == company.tenant_id))
        if fiscal_year is None:
            raise HTTPException(409, "Fiscal year for the posting period was not found")
        return settings, company.tenant_id, period, fiscal_year

    def _existing_source(self, db: Session, *, company_id: int, source_entity: str, source_id: int):
        company = db.scalar(select(Company).where(Company.id == company_id))
        if company is None:
            return None
        return db.scalar(select(JournalEntry).where(JournalEntry.tenant_id == company.tenant_id, JournalEntry.company_id == company_id, JournalEntry.source_module == "commerce", JournalEntry.source_entity == source_entity, JournalEntry.source_id == source_id))

    def _post(self, db: Session, *, company_id: int, user_id: int, entry_date: date, journal_id: int, entry_number: str, description: str, lines: list[dict], source_entity: str, source_id: int):
        validate_double_entry(lines)
        validate_source(source_module="commerce", source_entity=source_entity, source_id=source_id)
        settings, tenant_id, period, fiscal_year = self._context(db, company_id, entry_date)
        existing = db.scalar(select(JournalEntry).where(JournalEntry.tenant_id == tenant_id, JournalEntry.company_id == company_id, JournalEntry.source_module == "commerce", JournalEntry.source_entity == source_entity, JournalEntry.source_id == source_id))
        if existing:
            return existing
        journal = db.scalar(select(AccountingJournal).where(AccountingJournal.id == journal_id, AccountingJournal.company_id == company_id, AccountingJournal.tenant_id == tenant_id, AccountingJournal.is_active.is_(True)))
        if journal is None:
            raise HTTPException(409, "Configured accounting journal was not found")
        entry = journal_service.create_draft(db, tenant_id=tenant_id, company_id=company_id, branch_id=settings.default_branch_id, journal_id=journal_id, fiscal_year_id=fiscal_year.id, period_id=period.id, entry_number=entry_number, entry_date=entry_date, description=description, lines=lines, user_id=user_id, source_module="commerce", source_entity=source_entity, source_id=source_id, commit=False)
        journal_service.submit(db, tenant_id=tenant_id, entry_id=entry.id, user_id=user_id, commit=False)
        if journal.requires_approval:
            journal_service.approve(db, tenant_id=tenant_id, entry_id=entry.id, user_id=user_id, commit=False)
        if settings.auto_post and journal.auto_post:
            journal_service.post(db, tenant_id=tenant_id, entry_id=entry.id, user_id=user_id, commit=False)
        return entry

    def post_sales_invoice(self, db, document, user_id: int):
        settings = self._settings(db, document.company_id)
        lines = [{"account_combination_id": settings.ar_account_id, "debit": Decimal(document.total), "credit": 0, "description": f"AR {document.number}"}, {"account_combination_id": settings.sales_account_id, "debit": 0, "credit": Decimal(document.subtotal), "description": f"Sales {document.number}"}]
        if Decimal(document.tax_total or 0):
            lines.append({"account_combination_id": settings.output_vat_account_id, "debit": 0, "credit": Decimal(document.tax_total), "description": f"Output VAT {document.number}"})
        return self._post(db, company_id=document.company_id, user_id=user_id, entry_date=document.document_date, journal_id=settings.sales_journal_id, entry_number=f"SI-{document.id}", description=f"Sales invoice {document.number}", lines=lines, source_entity="sales_invoice", source_id=document.id)

    def post_sales_credit_note(self, db, document, user_id: int):
        settings = self._settings(db, document.company_id)
        lines = [{"account_combination_id": settings.sales_account_id, "debit": Decimal(document.subtotal), "credit": 0, "description": f"Sales return {document.number}"}]
        if Decimal(document.tax_total or 0):
            lines.append({"account_combination_id": settings.output_vat_account_id, "debit": Decimal(document.tax_total), "credit": 0, "description": f"Output VAT reversal {document.number}"})
        lines.append({"account_combination_id": settings.ar_account_id, "debit": 0, "credit": Decimal(document.total), "description": f"AR reduction {document.number}"})
        return self._post(db, company_id=document.company_id, user_id=user_id, entry_date=document.document_date, journal_id=settings.sales_journal_id, entry_number=f"SCN-{document.id}", description=f"Sales credit note {document.number}", lines=lines, source_entity="sales_credit_note", source_id=document.id)

    def _purchase_stock_expense_totals(self, db, document):
        stock_total = Decimal("0")
        expense_total = Decimal("0")
        for line in document.lines:
            item = db.scalar(select(InventoryItem).where(InventoryItem.id == line.item_id, InventoryItem.company_id == document.company_id))
            net = Decimal(line.quantity) * Decimal(line.unit_price) * (Decimal("100") - Decimal(line.discount_percent or 0)) / Decimal("100")
            if item and item.item_type in {"stockable", "consumable"}:
                stock_total += net
            else:
                expense_total += net
        return stock_total, expense_total

    def _linked_receipt_ids(self, db: Session, document) -> list[int]:
        return list(db.scalars(select(PurchaseBillReceiptLink.receipt_id).where(PurchaseBillReceiptLink.company_id == document.company_id, PurchaseBillReceiptLink.bill_id == document.id).order_by(PurchaseBillReceiptLink.receipt_id)).all())

    def _allocate_receipt_value(self, db: Session, *, document, line) -> Decimal:
        receipt_ids = self._linked_receipt_ids(db, document)
        if not receipt_ids:
            return Decimal("0")
        receipt_predicates = [InventoryStockMove.source_id.like(f"{rid}:%") for rid in receipt_ids]
        moves = list(db.scalars(select(InventoryStockMove).where(InventoryStockMove.company_id == document.company_id, InventoryStockMove.source_module == "commerce", InventoryStockMove.source_entity == "purchase_receipt", InventoryStockMove.status == "posted", InventoryStockMove.item_id == line.item_id, InventoryStockMove.variant_id == line.variant_id, *receipt_predicates).with_for_update()).all())
        required = Decimal(line.quantity)
        remaining = required
        value = Decimal("0")
        for move in moves:
            allocated = db.scalar(select(func.coalesce(func.sum(PurchaseBillReceiptAllocation.quantity), 0)).where(PurchaseBillReceiptAllocation.company_id == document.company_id, PurchaseBillReceiptAllocation.receipt_move_id == move.id)) or Decimal("0")
            available = Decimal(move.quantity) - Decimal(allocated)
            if available <= 0:
                continue
            take = min(available, remaining)
            value += take * Decimal(move.unit_cost or 0)
            db.add(PurchaseBillReceiptAllocation(company_id=document.company_id, bill_line_id=line.id, receipt_move_id=move.id, quantity=take, unit_cost=Decimal(move.unit_cost or 0)))
            remaining -= take
            if remaining <= 0:
                break
        if remaining > 0:
            raise HTTPException(status_code=409, detail=f"Receipt quantity is insufficient for bill line {line.id}; link sufficient received quantity before posting the bill")
        return value

    def post_purchase_receipt(self, db, document, user_id: int):
        settings = self._settings(db, document.company_id)
        moves = list(db.scalars(select(InventoryStockMove).where(InventoryStockMove.company_id == document.company_id, InventoryStockMove.source_module == "commerce", InventoryStockMove.source_entity == "purchase_receipt", InventoryStockMove.source_id.like(f"{document.id}:%"), InventoryStockMove.status == "posted")))
        inventory_value = sum((Decimal(move.quantity) * Decimal(move.unit_cost or 0) for move in moves), Decimal("0"))
        if inventory_value <= 0:
            return None
        return self._post(db, company_id=document.company_id, user_id=user_id, entry_date=document.document_date, journal_id=settings.purchase_journal_id, entry_number=f"GRN-{document.id}", description=f"Goods receipt {document.number}", lines=[{"account_combination_id": settings.inventory_account_id, "debit": inventory_value, "credit": 0, "description": f"Inventory receipt {document.number}"}, {"account_combination_id": settings.grni_account_id, "debit": 0, "credit": inventory_value, "description": f"GRNI {document.number}"}], source_entity="purchase_receipt_accounting", source_id=document.id)

    def post_purchase_bill(self, db, document, user_id: int):
        settings = self._settings(db, document.company_id)
        existing = self._existing_source(db, company_id=document.company_id, source_entity="purchase_bill", source_id=document.id)
        if existing:
            return existing
        stock_total, expense_total = self._purchase_stock_expense_totals(db, document)
        linked_receipts = self._linked_receipt_ids(db, document)
        lines = []
        receipt_value = Decimal("0")
        if stock_total:
            if linked_receipts:
                for line in document.lines:
                    item = db.scalar(select(InventoryItem).where(InventoryItem.id == line.item_id, InventoryItem.company_id == document.company_id))
                    if item and item.item_type in {"stockable", "consumable"}:
                        receipt_value += self._allocate_receipt_value(db, document=document, line=line)
                if receipt_value <= 0 and stock_total > 0:
                    raise HTTPException(409, "Linked purchase receipts have no inventory valuation")
                grni_value = receipt_value
                lines.append({"account_combination_id": settings.grni_account_id, "debit": grni_value, "credit": 0, "description": f"GRNI clearing {document.number}"})
                variance = stock_total - receipt_value
                if variance != 0 and settings.purchase_price_variance_account_id is None:
                    raise HTTPException(409, "Purchase Price Variance account is required when bill and receipt valuations differ")
                if variance > 0:
                    lines.append({"account_combination_id": settings.purchase_price_variance_account_id, "debit": variance, "credit": 0, "description": f"Purchase price variance {document.number}"})
                elif variance < 0:
                    lines.append({"account_combination_id": settings.purchase_price_variance_account_id, "debit": 0, "credit": -variance, "description": f"Purchase price variance credit {document.number}"})
            else:
                lines.append({"account_combination_id": settings.inventory_account_id, "debit": stock_total, "credit": 0, "description": f"Inventory {document.number}"})
        if expense_total:
            lines.append({"account_combination_id": settings.purchase_account_id, "debit": expense_total, "credit": 0, "description": f"Purchase expense {document.number}"})
        if Decimal(document.tax_total or 0):
            lines.append({"account_combination_id": settings.input_vat_account_id, "debit": Decimal(document.tax_total), "credit": 0, "description": f"Input VAT {document.number}"})
        lines.append({"account_combination_id": settings.ap_account_id, "debit": 0, "credit": Decimal(document.total), "description": f"AP {document.number}"})
        return self._post(db, company_id=document.company_id, user_id=user_id, entry_date=document.document_date, journal_id=settings.purchase_journal_id, entry_number=f"PB-{document.id}", description=f"Purchase bill {document.number}", lines=lines, source_entity="purchase_bill", source_id=document.id)

    def post_purchase_debit_note(self, db, document, user_id: int):
        settings = self._settings(db, document.company_id)
        stock_total, expense_total = self._purchase_stock_expense_totals(db, document)
        lines = []
        if stock_total:
            lines.append({"account_combination_id": settings.inventory_account_id, "debit": 0, "credit": stock_total, "description": f"Inventory reduction {document.number}"})
        if expense_total:
            lines.append({"account_combination_id": settings.purchase_account_id, "debit": 0, "credit": expense_total, "description": f"Purchase expense reversal {document.number}"})
        if Decimal(document.tax_total or 0):
            lines.append({"account_combination_id": settings.input_vat_account_id, "debit": 0, "credit": Decimal(document.tax_total), "description": f"Input VAT reversal {document.number}"})
        lines.append({"account_combination_id": settings.ap_account_id, "debit": Decimal(document.total), "credit": 0, "description": f"AP reduction {document.number}"})
        return self._post(db, company_id=document.company_id, user_id=user_id, entry_date=document.document_date, journal_id=settings.purchase_journal_id, entry_number=f"PDN-{document.id}", description=f"Purchase debit note {document.number}", lines=lines, source_entity="purchase_debit_note", source_id=document.id)

    def post_sales_delivery_cogs(self, db, document, user_id: int):
        settings = self._settings(db, document.company_id)
        moves = list(db.scalars(select(InventoryStockMove).where(InventoryStockMove.company_id == document.company_id, InventoryStockMove.source_module == "commerce", InventoryStockMove.source_entity == "sales_delivery", InventoryStockMove.source_id.like(f"{document.id}:%"), InventoryStockMove.status == "posted")))
        total = sum((Decimal(m.quantity) * Decimal(m.unit_cost or 0) for m in moves), Decimal("0"))
        if total <= 0:
            return None
        return self._post(db, company_id=document.company_id, user_id=user_id, entry_date=document.document_date, journal_id=settings.sales_journal_id, entry_number=f"COGS-{document.id}", description=f"COGS for delivery {document.number}", lines=[{"account_combination_id": settings.cogs_account_id, "debit": total, "credit": 0}, {"account_combination_id": settings.inventory_account_id, "debit": 0, "credit": total}], source_entity="sales_cogs", source_id=document.id)

    def post_payment(self, db, payment, document, user_id: int):
        settings = self._settings(db, payment.company_id)
        control = settings.ar_account_id if payment.document_kind == "sale" else settings.ap_account_id
        gross = Decimal(payment.amount)
        wht = Decimal(payment.wht_amount or 0)
        cash = gross - wht
        if wht and settings.wht_account_id is None:
            raise HTTPException(409, "WHT account is required when withholding tax is used")
        if payment.document_kind == "sale":
            lines = [{"account_combination_id": settings.default_payment_account_id, "debit": cash, "credit": 0}]
            if wht:
                lines.append({"account_combination_id": settings.wht_account_id, "debit": wht, "credit": 0})
            lines.append({"account_combination_id": control, "debit": 0, "credit": gross})
        else:
            lines = [{"account_combination_id": control, "debit": gross, "credit": 0}]
            if wht:
                lines.append({"account_combination_id": settings.wht_account_id, "debit": 0, "credit": wht})
            lines.append({"account_combination_id": settings.default_payment_account_id, "debit": 0, "credit": cash})
        return self._post(db, company_id=payment.company_id, user_id=user_id, entry_date=payment.payment_date, journal_id=settings.payment_journal_id, entry_number=f"PAY-{payment.id}", description=f"Payment {payment.id}", lines=lines, source_entity="payment", source_id=payment.id)

    def post_payment_reversal(self, db, payment, document, user_id: int, reversal_date: date):
        settings = self._settings(db, payment.company_id)
        original = self._existing_source(db, company_id=payment.company_id, source_entity="payment", source_id=payment.id)
        if original is None:
            raise HTTPException(409, "Original payment accounting entry was not found")
        lines = [{"account_combination_id": line.account_combination_id, "debit": Decimal(line.credit), "credit": Decimal(line.debit), "description": f"Payment reversal {payment.id}"} for line in original.lines]
        return self._post(db, company_id=payment.company_id, user_id=user_id, entry_date=reversal_date, journal_id=settings.payment_journal_id, entry_number=f"PAY-REV-{payment.id}", description=f"Payment reversal {payment.id}", lines=lines, source_entity="payment_reversal", source_id=payment.id)


commerce_accounting_service = CommerceAccountingService()
