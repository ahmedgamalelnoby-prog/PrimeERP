from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.accounting.fiscal_years.repositories.fiscal_year_repository import fiscal_year_repository
from app.modules.accounting.journals.models import JournalEntry, JournalEntryLine
from app.modules.accounting.journals.repositories.journal_repository import journal_repository


class JournalService:
    """Application boundary for journal-entry lifecycle and posting rules."""

    def list_journals(self, db: Session, tenant_id: int, company_id: int):
        return journal_repository.list_journals(db, tenant_id, company_id)

    def list_entries(self, db: Session, tenant_id: int, company_id: int, **filters):
        return journal_repository.list_entries(db, tenant_id, company_id, **filters)

    def get_entry(self, db: Session, tenant_id: int, entry_id: int) -> JournalEntry:
        entry = journal_repository.get_entry(db, entry_id, tenant_id)
        if entry is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal entry not found")
        return entry

    def create_draft(self, db: Session, *, tenant_id: int, company_id: int, branch_id: int, journal_id: int, fiscal_year_id: int, period_id: int, entry_number: str, entry_date: date, description: str, lines: list[dict], user_id: int | None = None, currency_code: str = "EGP", exchange_rate: Decimal = Decimal("1"), reference: str | None = None, source_module: str | None = None, source_entity: str | None = None, source_id: int | None = None, commit: bool = True) -> JournalEntry:
        journal = journal_repository.get_journal(db, journal_id, tenant_id, company_id)
        if journal is None or not journal.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Accounting journal not found")
        if not journal.allow_manual_entries and source_module != "commerce":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Manual entries are disabled for this journal")
        if len(lines) < 2:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Journal entry requires at least two lines")
        if exchange_rate <= 0:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Exchange rate must be positive")
        period = fiscal_year_repository.get_period_by_id(db, period_id, tenant_id)
        if period is None or period.company_id != company_id or period.fiscal_year_id != fiscal_year_id:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Fiscal period does not belong to the selected company and fiscal year")
        if not (period.start_date <= entry_date <= period.end_date):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Entry date is outside the selected accounting period")

        debit = Decimal("0")
        credit = Decimal("0")
        entry = JournalEntry(tenant_id=tenant_id, company_id=company_id, branch_id=branch_id, journal_id=journal_id, fiscal_year_id=fiscal_year_id, period_id=period_id, entry_number=entry_number.strip(), entry_date=entry_date, description=description.strip(), currency_code=currency_code.upper(), exchange_rate=exchange_rate, reference=reference.strip() if reference else None, source_module=source_module, source_entity=source_entity, source_id=source_id, created_by=user_id, status="draft")
        for number, payload in enumerate(lines, start=1):
            line_debit = Decimal(str(payload.get("debit", 0)))
            line_credit = Decimal(str(payload.get("credit", 0)))
            if line_debit < 0 or line_credit < 0 or (line_debit > 0 and line_credit > 0) or (line_debit == 0 and line_credit == 0):
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid amount on journal line {number}")
            debit += line_debit
            credit += line_credit
            entry.lines.append(JournalEntryLine(tenant_id=tenant_id, line_number=number, account_combination_id=int(payload["account_combination_id"]), department_id=payload.get("department_id"), cost_center_id=payload.get("cost_center_id"), description=payload.get("description"), reference=payload.get("reference"), debit=line_debit, credit=line_credit, currency_code=currency_code.upper(), exchange_rate=exchange_rate, base_debit=line_debit * exchange_rate, base_credit=line_credit * exchange_rate))
        if debit != credit:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Journal entry must be balanced: total debit must equal total credit")
        entry.total_debit = debit
        entry.total_credit = credit
        db.add(entry)
        db.flush()
        if commit:
            db.commit()
            db.refresh(entry)
        return entry

    def submit(self, db: Session, *, tenant_id: int, entry_id: int, user_id: int, commit: bool = True) -> JournalEntry:
        entry = self._locked_entry(db, tenant_id, entry_id)
        if entry.status != "draft":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only draft entries can be submitted")
        entry.status = "pending"; entry.submitted_by = user_id; entry.submitted_at = datetime.now(timezone.utc)
        db.flush()
        if commit:
            db.commit(); db.refresh(entry)
        return entry

    def approve(self, db: Session, *, tenant_id: int, entry_id: int, user_id: int, commit: bool = True) -> JournalEntry:
        entry = self._locked_entry(db, tenant_id, entry_id)
        if entry.status != "pending":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only pending entries can be approved")
        entry.status = "approved"; entry.approved_by = user_id; entry.approved_at = datetime.now(timezone.utc)
        db.flush()
        if commit:
            db.commit(); db.refresh(entry)
        return entry

    def post(self, db: Session, *, tenant_id: int, entry_id: int, user_id: int, commit: bool = True) -> JournalEntry:
        entry = self._locked_entry(db, tenant_id, entry_id)
        if entry.status not in {"approved", "pending"}:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only approved or pending entries can be posted")
        if entry.status == "pending" and entry.journal.requires_approval:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Journal approval is required before posting")
        period = fiscal_year_repository.get_period_by_id(db, entry.period_id, tenant_id, for_update=True)
        if period is None or period.status != "open" or not period.allow_posting:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Accounting period is not open for posting")
        if not (period.start_date <= entry.entry_date <= period.end_date):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Entry date is outside the posting period")
        if entry.total_debit != entry.total_credit:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Cannot post an unbalanced journal entry")
        entry.status = "posted"; entry.posting_date = entry.entry_date; entry.posted_by = user_id; entry.posted_at = datetime.now(timezone.utc)
        db.flush()
        if commit:
            db.commit(); db.refresh(entry)
        return entry

    def cancel(self, db: Session, *, tenant_id: int, entry_id: int, user_id: int, commit: bool = True) -> JournalEntry:
        entry = self._locked_entry(db, tenant_id, entry_id)
        if entry.status == "posted":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Posted entries cannot be cancelled; use a reversal entry")
        if entry.status in {"cancelled", "reversed"}:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Journal entry is already closed")
        entry.status = "cancelled"; entry.cancelled_by = user_id; entry.cancelled_at = datetime.now(timezone.utc)
        db.flush()
        if commit:
            db.commit(); db.refresh(entry)
        return entry

    @staticmethod
    def _locked_entry(db: Session, tenant_id: int, entry_id: int) -> JournalEntry:
        entry = journal_repository.get_entry(db, entry_id, tenant_id, for_update=True)
        if entry is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal entry not found")
        return entry


journal_service = JournalService()
