from datetime import date
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.modules.accounting.fiscal_years.services.fiscal_year_service import fiscal_year_service
from app.modules.accounting.journals.models import JournalEntry
from app.modules.accounting.journals.services.journal_service import journal_service
from app.modules.commerce.accounting_models import CommerceAccountingSettings
from app.modules.companies.models import Company
from app.modules.treasury.models import Cheque

class TreasuryAccountingService:
    """Accounting bridge for treasury cheque lifecycle.

    Uses the company's existing commerce accounting configuration so treasury
    remains part of the same GL configuration surface. The default payment
    account acts as the configured bank/cheque clearing account.
    """
    def _context(self, db: Session, cheque: Cheque, when: date):
        company = db.scalar(select(Company).where(Company.id == cheque.company_id, Company.is_active.is_(True)))
        if company is None or company.tenant_id is None:
            raise HTTPException(409, "Company accounting context is missing")
        settings = db.scalar(select(CommerceAccountingSettings).where(CommerceAccountingSettings.company_id == cheque.company_id))
        if settings is None:
            raise HTTPException(409, "Commerce accounting configuration is required before treasury can post to GL")
        period = fiscal_year_service.assert_open_for_date(db, company_id=cheque.company_id, posting_date=when)
        return company, settings, period

    def _post(self, db: Session, cheque: Cheque, *, when: date, user_id: int, event_key: str, description: str, lines: list[dict]):
        company, settings, period = self._context(db, cheque, when)
        existing = db.scalar(select(JournalEntry).where(
            JournalEntry.tenant_id == company.tenant_id,
            JournalEntry.company_id == cheque.company_id,
            JournalEntry.source_module == "treasury",
            JournalEntry.source_entity == f"cheque_event:{event_key}",
            JournalEntry.source_id == f"{cheque.id}:{event_key}",
        ))
        if existing is not None:
            return existing
        entry = journal_service.create_draft(
            db,
            tenant_id=company.tenant_id,
            company_id=cheque.company_id,
            branch_id=settings.default_branch_id,
            journal_id=settings.cash_journal_id,
            fiscal_year_id=period.fiscal_year_id,
            period_id=period.id,
            entry_number=f"CHQ-{cheque.id}-{event_key[:12]}",
            entry_date=when,
            description=description,
            lines=lines,
            user_id=user_id,
            source_module="treasury",
            source_entity=f"cheque_event:{event_key}",
            source_id=cheque.id,
            commit=False,
            currency_code=cheque.currency,
        )
        journal_service.submit(db, tenant_id=company.tenant_id, entry_id=entry.id, user_id=user_id, commit=False)
        if not entry.journal.requires_approval:
            journal_service.post(db, tenant_id=company.tenant_id, entry_id=entry.id, user_id=user_id, commit=False)
        return entry

    def created(self, db: Session, cheque: Cheque, user_id: int):
        settings = db.scalar(select(CommerceAccountingSettings).where(CommerceAccountingSettings.company_id == cheque.company_id))
        if settings is None:
            raise HTTPException(409, "Commerce accounting configuration is required before creating a GL-linked cheque")
        control = settings.ar_account_id if cheque.direction == "received" else settings.ap_account_id
        if cheque.direction == "received":
            lines = [
                {"account_combination_id": settings.default_payment_account_id, "debit": Decimal(cheque.amount), "credit": 0, "description": f"Cheque in hand {cheque.cheque_number}"},
                {"account_combination_id": control, "debit": 0, "credit": Decimal(cheque.amount), "description": f"Cheque against AR {cheque.cheque_number}"},
            ]
        else:
            lines = [
                {"account_combination_id": control, "debit": Decimal(cheque.amount), "credit": 0, "description": f"Cheque against AP {cheque.cheque_number}"},
                {"account_combination_id": settings.default_payment_account_id, "debit": 0, "credit": Decimal(cheque.amount), "description": f"Cheque payable {cheque.cheque_number}"},
            ]
        return self._post(db, cheque, when=cheque.cheque_date, user_id=user_id, event_key="created", description=f"Treasury cheque {cheque.cheque_number}", lines=lines)

    def cancellation(self, db: Session, cheque: Cheque, when: date, user_id: int, event_key: str):
        settings = db.scalar(select(CommerceAccountingSettings).where(CommerceAccountingSettings.company_id == cheque.company_id))
        if settings is None:
            raise HTTPException(409, "Commerce accounting configuration is required for treasury reversal")
        control = settings.ar_account_id if cheque.direction == "received" else settings.ap_account_id
        if cheque.direction == "received":
            lines = [
                {"account_combination_id": control, "debit": Decimal(cheque.amount), "credit": 0},
                {"account_combination_id": settings.default_payment_account_id, "debit": 0, "credit": Decimal(cheque.amount)},
            ]
        else:
            lines = [
                {"account_combination_id": settings.default_payment_account_id, "debit": Decimal(cheque.amount), "credit": 0},
                {"account_combination_id": control, "debit": 0, "credit": Decimal(cheque.amount)},
            ]
        return self._post(db, cheque, when=when, user_id=user_id, event_key=event_key, description=f"Treasury cheque reversal {cheque.cheque_number}", lines=lines)

treasury_accounting_service = TreasuryAccountingService()
