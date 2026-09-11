from datetime import date
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.accounting.fiscal_years.models import AccountingPeriod, FiscalYear
from app.modules.accounting.journals.models import AccountingJournal
from app.modules.accounting.journals.services.journal_service import journal_service
from app.modules.commerce.accounting_models import CommerceAccountingSettings
from app.modules.companies.models import Company


class CommerceAccountingService:
    def _settings(self, db: Session, company_id: int) -> CommerceAccountingSettings:
        settings = db.scalar(select(CommerceAccountingSettings).where(CommerceAccountingSettings.company_id == company_id))
        if settings is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Commerce accounting configuration is missing for this company")
        return settings

    def _context(self, db: Session, company_id: int, entry_date: date):
        settings = self._settings(db, company_id)
        company = db.scalar(select(Company).where(Company.id == company_id))
        if company is None:
            raise HTTPException(status_code=404, detail="Company not found")
        period = db.scalar(select(AccountingPeriod).where(
            AccountingPeriod.company_id == company_id,
            AccountingPeriod.start_date <= entry_date,
            AccountingPeriod.end_date >= entry_date,
            AccountingPeriod.status == "open",
            AccountingPeriod.allow_posting.is_(True),
        ).order_by(AccountingPeriod.period_number.desc()))
        if period is None:
            raise HTTPException(status_code=409, detail="No open posting period exists for the document date")
        fiscal_year = db.scalar(select(FiscalYear).where(FiscalYear.id == period.fiscal_year_id, FiscalYear.company_id == company_id))
        if fiscal_year is None:
            raise HTTPException(status_code=409, detail="Fiscal year for the posting period was not found")
        branch = db.scalar(select(Company.branches.property.mapper.class_).where(Company.branches.property.mapper.class_.id == settings.default_branch_id))
        if branch is None:
            raise HTTPException(status_code=409, detail="Configured accounting branch was not found")
        return settings, company.tenant_id, period, fiscal_year

    def _post(self, db: Session, *, company_id: int, user_id: int, entry_date: date, journal_id: int, entry_number: str, description: str, lines: list[dict], source_entity: str, source_id: int):
        settings, tenant_id, period, fiscal_year = self._context(db, company_id, entry_date)
        existing = db.scalar(select(__import__("app.modules.accounting.journals.models", fromlist=["JournalEntry"]).JournalEntry).where(
            __import__("app.modules.accounting.journals.models", fromlist=["JournalEntry"]).JournalEntry.tenant_id == tenant_id,
            __import__("app.modules.accounting.journals.models", fromlist=["JournalEntry"]).JournalEntry.source_module == "commerce",
            __import__("app.modules.accounting.journals.models", fromlist=["JournalEntry"]).JournalEntry.source_entity == source_entity,
            __import__("app.modules.accounting.journals.models", fromlist=["JournalEntry"]).JournalEntry.source_id == source_id,
            __import__("app.modules.accounting.journals.models", fromlist=["JournalEntry"]).JournalEntry.status.in_(["pending", "approved", "posted"]),
        ))
        if existing:
            return existing
        journal = db.scalar(select(AccountingJournal).where(AccountingJournal.id == journal_id, AccountingJournal.company_id == company_id, AccountingJournal.tenant_id == tenant_id, AccountingJournal.is_active.is_(True)))
        if journal is None:
            raise HTTPException(status_code=409, detail="Configured accounting journal was not found")
        entry = journal_service.create_draft(
            db, tenant_id=tenant_id, company_id=company_id, branch_id=settings.default_branch_id,
            journal_id=journal_id, fiscal_year_id=fiscal_year.id, period_id=period.id,
            entry_number=entry_number, entry_date=entry_date, description=description,
            lines=lines, user_id=user_id, source_module="commerce", source_entity=source_entity, source_id=source_id,
        )
        journal_service.submit(db, tenant_id=tenant_id, entry_id=entry.id, user_id=user_id)
        if journal.requires_approval:
            journal_service.approve(db, tenant_id=tenant_id, entry_id=entry.id, user_id=user_id)
        journal_service.post(db, tenant_id=tenant_id, entry_id=entry.id, user_id=user_id)
        return entry

    def post_sales_invoice(self, db: Session, document, user_id: int):
        settings = self._settings(db, document.company_id)
        lines = [{"account_combination_id": settings.ar_account_id, "debit": Decimal(document.total), "credit": 0, "description": f"AR {document.number}"},
                 {"account_combination_id": settings.sales_account_id, "debit": 0, "credit": Decimal(document.subtotal), "description": f"Sales {document.number}"}]
        if Decimal(document.tax_total or 0):
            lines.append({"account_combination_id": settings.output_vat_account_id, "debit": 0, "credit": Decimal(document.tax_total), "description": f"Output VAT {document.number}"})
        return self._post(db, company_id=document.company_id, user_id=user_id, entry_date=document.document_date, journal_id=settings.sales_journal_id, entry_number=f"SI-{document.id}", description=f"Sales invoice {document.number}", lines=lines, source_entity="sales_invoice", source_id=document.id)

    def post_purchase_bill(self, db: Session, document, user_id: int):
        settings = self._settings(db, document.company_id)
        lines = [{"account_combination_id": settings.purchase_account_id, "debit": Decimal(document.subtotal), "credit": 0, "description": f"Purchase {document.number}"}]
        if Decimal(document.tax_total or 0):
            lines.append({"account_combination_id": settings.input_vat_account_id, "debit": Decimal(document.tax_total), "credit": 0, "description": f"Input VAT {document.number}"})
        lines.append({"account_combination_id": settings.ap_account_id, "debit": 0, "credit": Decimal(document.total), "description": f"AP {document.number}"})
        return self._post(db, company_id=document.company_id, user_id=user_id, entry_date=document.document_date, journal_id=settings.purchase_journal_id, entry_number=f"PB-{document.id}", description=f"Purchase bill {document.number}", lines=lines, source_entity="purchase_bill", source_id=document.id)

    def post_payment(self, db: Session, payment, document, user_id: int):
        settings = self._settings(db, payment.company_id)
        is_sale = payment.document_kind == "sale"
        control = settings.ar_account_id if is_sale else settings.ap_account_id
        if is_sale:
            lines = [{"account_combination_id": settings.default_payment_account_id, "debit": Decimal(payment.amount), "credit": 0, "description": f"Receipt {payment.reference or payment.id}"}, {"account_combination_id": control, "debit": 0, "credit": Decimal(payment.amount), "description": f"AR settlement {document.number}"}]
        else:
            lines = [{"account_combination_id": control, "debit": Decimal(payment.amount), "credit": 0, "description": f"AP settlement {document.number}"}, {"account_combination_id": settings.default_payment_account_id, "debit": 0, "credit": Decimal(payment.amount), "description": f"Payment {payment.reference or payment.id}"}]
        return self._post(db, company_id=payment.company_id, user_id=user_id, entry_date=payment.payment_date, journal_id=settings.cash_journal_id, entry_number=f"PAY-{payment.id}", description=f"Commerce payment {payment.id}", lines=lines, source_entity="commerce_payment", source_id=payment.id)


commerce_accounting_service = CommerceAccountingService()
