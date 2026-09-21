from datetime import date
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.accounting.compliance_controls import validate_double_entry, validate_source
from app.modules.accounting.fiscal_years.models import AccountingPeriod, FiscalYear
from app.modules.accounting.journals.models import AccountingJournal, JournalEntry
from app.modules.accounting.journals.services.journal_service import journal_service
from app.modules.branches.models import Branch
from app.modules.commerce.accounting_models import CommerceAccountingSettings
from app.modules.companies.models import Company
from app.modules.treasury.accounting_models import TreasuryAccountingSettings
from app.modules.treasury.models import Cheque, ChequeEvent


class TreasuryAccountingService:
    def _context(self, db: Session, company_id: int, entry_date: date):
        company = db.scalar(select(Company).where(Company.id == company_id))
        if company is None:
            raise HTTPException(404, "Company not found")
        commerce = db.scalar(select(CommerceAccountingSettings).where(CommerceAccountingSettings.company_id == company_id))
        settings = db.scalar(select(TreasuryAccountingSettings).where(TreasuryAccountingSettings.company_id == company_id))
        if commerce is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Commerce accounting configuration is missing for this company")
        if settings is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Treasury accounting configuration is missing for this company")
        branch = db.scalar(select(Branch).where(Branch.id == settings.default_branch_id, Branch.company_id == company_id, Branch.tenant_id == company.tenant_id, Branch.is_active.is_(True)))
        if branch is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Configured treasury accounting branch was not found")
        period = db.scalar(select(AccountingPeriod).where(AccountingPeriod.company_id == company_id, AccountingPeriod.tenant_id == company.tenant_id, AccountingPeriod.start_date <= entry_date, AccountingPeriod.end_date >= entry_date, AccountingPeriod.status == "open", AccountingPeriod.allow_posting.is_(True)).order_by(AccountingPeriod.period_number.desc()))
        if period is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No open posting period exists for the cheque event date")
        fiscal_year = db.scalar(select(FiscalYear).where(FiscalYear.id == period.fiscal_year_id, FiscalYear.company_id == company_id, FiscalYear.tenant_id == company.tenant_id))
        if fiscal_year is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Fiscal year for the posting period was not found")
        return company, commerce, settings, branch, period, fiscal_year

    @staticmethod
    def _account_state(settings: TreasuryAccountingSettings, cheque: Cheque) -> int:
        if cheque.direction == "issued":
            return settings.issued_cheques_account_id
        if cheque.status in {"received", "deposited"}:
            return settings.received_cheques_account_id
        if cheque.status in {"under_collection", "resubmitted"}:
            return settings.under_collection_account_id
        if cheque.status == "returned":
            return settings.returned_cheques_account_id
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"No treasury accounting state exists for cheque status {cheque.status}")

    def _lines_for_event(self, commerce, settings, cheque: Cheque, event: ChequeEvent):
        amount = Decimal(str(cheque.amount))
        before = event.from_status
        after = event.to_status
        if event.event_type == "created":
            if cheque.direction == "received":
                return [
                    {"account_combination_id": settings.received_cheques_account_id, "debit": amount, "credit": 0, "description": f"Cheque received {cheque.cheque_number}"},
                    {"account_combination_id": commerce.ar_account_id, "debit": 0, "credit": amount, "description": f"AR settled by cheque {cheque.cheque_number}"},
                ]
            return [
                {"account_combination_id": commerce.ap_account_id, "debit": amount, "credit": 0, "description": f"AP settled by cheque {cheque.cheque_number}"},
                {"account_combination_id": settings.issued_cheques_account_id, "debit": 0, "credit": amount, "description": f"Cheque issued {cheque.cheque_number}"},
            ]
        if event.event_type == "deposited":
            return [{"account_combination_id": settings.bank_account_id, "debit": amount, "credit": 0}, {"account_combination_id": settings.received_cheques_account_id, "debit": 0, "credit": amount}]
        if event.event_type == "under_collection":
            return [{"account_combination_id": settings.under_collection_account_id, "debit": amount, "credit": 0}, {"account_combination_id": settings.bank_account_id, "debit": 0, "credit": amount}]
        if event.event_type == "collected":
            return [{"account_combination_id": settings.bank_account_id, "debit": amount, "credit": 0}, {"account_combination_id": settings.under_collection_account_id, "debit": 0, "credit": amount}]
        if event.event_type == "returned":
            source = settings.under_collection_account_id if before in {"deposited", "under_collection", "resubmitted"} else settings.received_cheques_account_id
            return [{"account_combination_id": settings.returned_cheques_account_id, "debit": amount, "credit": 0}, {"account_combination_id": source, "debit": 0, "credit": amount}]
        if event.event_type == "resubmitted":
            return [{"account_combination_id": settings.under_collection_account_id, "debit": amount, "credit": 0}, {"account_combination_id": settings.returned_cheques_account_id, "debit": 0, "credit": amount}]
        if event.event_type == "withdrawn":
            source = settings.received_cheques_account_id if before in {"received", "deposited"} else self._account_state(settings, cheque)
            return [{"account_combination_id": commerce.ar_account_id, "debit": amount, "credit": 0}, {"account_combination_id": source, "debit": 0, "credit": amount}]
        if event.event_type == "cleared":
            return [{"account_combination_id": settings.issued_cheques_account_id, "debit": amount, "credit": 0}, {"account_combination_id": settings.bank_account_id, "debit": 0, "credit": amount}]
        if event.event_type == "reversed":
            if before == "issued":
                return [{"account_combination_id": settings.issued_cheques_account_id, "debit": amount, "credit": 0}, {"account_combination_id": commerce.ap_account_id, "debit": 0, "credit": amount}]
            if before == "cleared":
                return [{"account_combination_id": settings.bank_account_id, "debit": amount, "credit": 0}, {"account_combination_id": settings.issued_cheques_account_id, "debit": 0, "credit": amount}]
            if before == "collected":
                return [{"account_combination_id": settings.under_collection_account_id, "debit": amount, "credit": 0}, {"account_combination_id": settings.bank_account_id, "debit": 0, "credit": amount}]
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"No accounting policy exists for cheque event {event.event_type} ({before} -> {after})")

    def post_event(self, db: Session, cheque: Cheque, event: ChequeEvent, user_id: int):
        company, commerce, settings, branch, period, fiscal_year = self._context(db, cheque.company_id, event.event_date)
        existing = db.scalar(select(JournalEntry).where(JournalEntry.tenant_id == company.tenant_id, JournalEntry.company_id == cheque.company_id, JournalEntry.source_module == "treasury", JournalEntry.source_entity == "cheque_event", JournalEntry.source_id == event.id))
        if existing:
            return existing
        journal = db.scalar(select(AccountingJournal).where(AccountingJournal.id == settings.journal_id, AccountingJournal.company_id == cheque.company_id, AccountingJournal.tenant_id == company.tenant_id, AccountingJournal.is_active.is_(True)))
        if journal is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Configured treasury accounting journal was not found")
        lines = self._lines_for_event(commerce, settings, cheque, event)
        validate_double_entry(lines)
        validate_source(source_module="treasury", source_entity="cheque_event", source_id=event.id)
        entry = journal_service.create_draft(db, tenant_id=company.tenant_id, company_id=cheque.company_id, branch_id=branch.id, journal_id=journal.id, fiscal_year_id=fiscal_year.id, period_id=period.id, entry_number=f"TR-{event.id}", entry_date=event.event_date, description=f"Treasury cheque {cheque.cheque_number}: {event.event_type}", lines=lines, user_id=user_id, source_module="treasury", source_entity="cheque_event", source_id=event.id, commit=False)
        journal_service.submit(db, tenant_id=company.tenant_id, entry_id=entry.id, user_id=user_id, commit=False)
        if journal.requires_approval:
            journal_service.approve(db, tenant_id=company.tenant_id, entry_id=entry.id, user_id=user_id, commit=False)
        if settings.auto_post and journal.auto_post:
            journal_service.post(db, tenant_id=company.tenant_id, entry_id=entry.id, user_id=user_id, commit=False)
        return entry


treasury_accounting_service = TreasuryAccountingService()
