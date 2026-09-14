from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.accounting.ifrs_cma_models import (
    AccountingPolicy, ChartOfAccount, FiscalPeriod, JournalEntry, JournalLine,
)


class IFRSCMAService:
    def ensure_policy(self, db: Session, company_id: int) -> AccountingPolicy:
        policy = db.scalar(select(AccountingPolicy).where(AccountingPolicy.company_id == company_id).with_for_update())
        if policy is None:
            policy = AccountingPolicy(company_id=company_id)
            db.add(policy)
            db.flush()
        return policy

    def validate_date_in_open_period(self, db: Session, company_id: int, entry_date: date) -> FiscalPeriod:
        period = db.scalar(select(FiscalPeriod).where(
            FiscalPeriod.company_id == company_id,
            FiscalPeriod.start_date <= entry_date,
            FiscalPeriod.end_date >= entry_date,
        ).with_for_update())
        if period is None:
            raise ValueError("No fiscal period exists for the journal entry date")
        if period.status != "open":
            raise ValueError("The fiscal period is not open")
        return period

    def validate_balanced_lines(self, lines: list[dict]) -> None:
        debit = sum((Decimal(str(x.get("debit", 0))) for x in lines), Decimal("0"))
        credit = sum((Decimal(str(x.get("credit", 0))) for x in lines), Decimal("0"))
        if not lines or debit <= 0 or credit <= 0 or debit != credit:
            raise ValueError("Journal entry must have equal positive total debits and credits")

    def create_draft(self, db: Session, *, company_id: int, entry_no: str, entry_date: date,
                     description: str, source_module: str, source_entity: str, source_id: str,
                     lines: list[dict]) -> JournalEntry:
        self.validate_balanced_lines(lines)
        period = self.validate_date_in_open_period(db, company_id, entry_date)
        if db.scalar(select(JournalEntry).where(
            JournalEntry.company_id == company_id,
            JournalEntry.source_module == source_module,
            JournalEntry.source_entity == source_entity,
            JournalEntry.source_id == source_id,
        )):
            raise ValueError("An accounting entry already exists for this source transaction")
        accounts = {x.id: x for x in db.scalars(select(ChartOfAccount).where(ChartOfAccount.company_id == company_id)).all()}
        for line in lines:
            account = accounts.get(line["account_id"])
            if account is None or not account.is_active:
                raise ValueError("Journal line contains an invalid account")
            if not account.allow_manual_posting and source_module == "manual":
                raise ValueError("Manual posting is not allowed to this control account")
        entry = JournalEntry(
            company_id=company_id, fiscal_period_id=period.id, entry_no=entry_no,
            entry_date=entry_date, description=description, source_module=source_module,
            source_entity=source_entity, source_id=source_id, status="draft",
        )
        db.add(entry)
        db.flush()
        for line in lines:
            db.add(JournalLine(journal_entry_id=entry.id, **line))
        db.flush()
        return entry

    def approve(self, db: Session, *, company_id: int, entry_id: int, user_id: int) -> JournalEntry:
        entry = db.scalar(select(JournalEntry).where(JournalEntry.id == entry_id, JournalEntry.company_id == company_id).with_for_update())
        if entry is None:
            raise ValueError("Journal entry not found")
        if entry.status != "draft":
            raise ValueError("Only draft entries can be approved")
        entry.status = "approved"
        entry.approved_by_user_id = user_id
        db.flush()
        return entry

    def post(self, db: Session, *, company_id: int, entry_id: int) -> JournalEntry:
        entry = db.scalar(select(JournalEntry).where(JournalEntry.id == entry_id, JournalEntry.company_id == company_id).with_for_update())
        if entry is None:
            raise ValueError("Journal entry not found")
        if entry.status != "approved":
            raise ValueError("Only approved entries can be posted")
        period = db.scalar(select(FiscalPeriod).where(FiscalPeriod.id == entry.fiscal_period_id).with_for_update())
        if period is None or period.status != "open":
            raise ValueError("The fiscal period is not open")
        lines = list(db.scalars(select(JournalLine).where(JournalLine.journal_entry_id == entry.id)).all())
        self.validate_balanced_lines([{"debit": x.debit, "credit": x.credit} for x in lines])
        entry.status = "posted"
        entry.posted_at = datetime.now(timezone.utc)
        db.flush()
        return entry


ifrs_cma_service = IFRSCMAService()
