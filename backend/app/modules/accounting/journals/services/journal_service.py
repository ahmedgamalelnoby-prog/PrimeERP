from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.accounting.chart_of_accounts.models import AccountCombination, AccountingCostCenter, AccountingDepartment
from app.modules.accounting.posting_engine import PostingLine, PostingValidationError, reversal_lines, validate_balanced
from app.modules.accounting.fiscal_years.repositories.fiscal_year_repository import fiscal_year_repository
from app.modules.accounting.journals.models import JournalEntry, JournalEntryLine
from app.modules.accounting.journals.repositories.journal_repository import journal_repository
from app.modules.branches.models import Branch
from app.modules.company_settings.service import get_company_setting


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

    def create_draft(self, db: Session, *, tenant_id: int, company_id: int, branch_id: int, journal_id: int, fiscal_year_id: int, period_id: int, entry_number: str, entry_date: date, description: str, lines: list[dict], user_id: int | None = None, currency_code: str | None = None, exchange_rate: Decimal = Decimal("1"), reference: str | None = None, source_module: str | None = None, source_entity: str | None = None, source_id: int | None = None, commit: bool = True) -> JournalEntry:
        journal = journal_repository.get_journal(db, journal_id, tenant_id, company_id)
        if journal is None or not journal.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Accounting journal not found")
        if not journal.allow_manual_entries and source_module is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Manual entries are disabled for this journal")
        if len(lines) < 2:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Journal entry requires at least two lines")
        if exchange_rate <= 0:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Exchange rate must be positive")
        base_currency = str(get_company_setting(db, company_id, "general.base_currency")).upper()
        allow_multi_currency = get_company_setting(db, company_id, "general.allow_multi_currency") is True
        currency_code = str(currency_code or base_currency).upper()
        if currency_code != base_currency and not allow_multi_currency:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Company policy does not allow foreign-currency journals (base currency: {base_currency})",
            )
        if currency_code == base_currency and exchange_rate != Decimal("1"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Base-currency journal entries must use an exchange rate of 1",
            )
        company_timezone = str(get_company_setting(db, company_id, "general.timezone"))
        company_today = datetime.now(ZoneInfo(company_timezone)).date()
        if get_company_setting(db, company_id, "accounting.allow_backdated_entries") is not True and entry_date < company_today:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Company policy does not allow backdated journal entries",
            )
        if get_company_setting(db, company_id, "general.require_cost_center") is True:
            missing_cost_center = [index + 1 for index, line in enumerate(lines) if line.get("cost_center_id") is None]
            if missing_cost_center:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={"message": "Company policy requires a cost center on every journal line", "line_numbers": missing_cost_center},
                )
        branch = db.scalar(select(Branch).where(Branch.id == branch_id, Branch.company_id == company_id, Branch.tenant_id == tenant_id, Branch.is_active.is_(True)))
        if branch is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Branch does not belong to the selected company and tenant")
        period = fiscal_year_repository.get_period_by_id(db, period_id, tenant_id)
        if period is None or period.company_id != company_id or period.fiscal_year_id != fiscal_year_id:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Fiscal period does not belong to the selected company and fiscal year")
        if not (period.start_date <= entry_date <= period.end_date):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Entry date is outside the selected accounting period")
        account_ids = {int(payload["account_combination_id"]) for payload in lines}
        accounts = db.scalars(select(AccountCombination).where(AccountCombination.id.in_(account_ids), AccountCombination.tenant_id == tenant_id, AccountCombination.company_id == company_id, AccountCombination.is_active.is_(True))).all()
        if len({account.id for account in accounts}) != len(account_ids):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Every account combination must belong to the selected company and be active")
        department_ids = {int(payload["department_id"]) for payload in lines if payload.get("department_id") is not None}
        if department_ids:
            departments = db.scalars(select(AccountingDepartment).where(AccountingDepartment.id.in_(department_ids), AccountingDepartment.tenant_id == tenant_id, AccountingDepartment.company_id == company_id, AccountingDepartment.is_active.is_(True))).all()
            if len(departments) != len(department_ids):
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Every department must belong to the selected company and be active")
        cost_center_ids = {int(payload["cost_center_id"]) for payload in lines if payload.get("cost_center_id") is not None}
        if cost_center_ids:
            cost_centers = db.scalars(select(AccountingCostCenter).where(AccountingCostCenter.id.in_(cost_center_ids), AccountingCostCenter.tenant_id == tenant_id, AccountingCostCenter.company_id == company_id, AccountingCostCenter.is_active.is_(True))).all()
            if len(cost_centers) != len(cost_center_ids):
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Every cost center must belong to the selected company and be active")
        posting_lines = [
            PostingLine(
                account_combination_id=int(payload["account_combination_id"]),
                debit=Decimal(str(payload.get("debit", 0))),
                credit=Decimal(str(payload.get("credit", 0))),
                department_id=payload.get("department_id"),
                cost_center_id=payload.get("cost_center_id"),
            )
            for payload in lines
        ]
        try:
            debit, credit = validate_balanced(posting_lines)
        except PostingValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc

        entry = JournalEntry(tenant_id=tenant_id, company_id=company_id, branch_id=branch_id, journal_id=journal_id, fiscal_year_id=fiscal_year_id, period_id=period_id, entry_number=entry_number.strip(), entry_date=entry_date, description=description.strip(), currency_code=currency_code.upper(), exchange_rate=exchange_rate, reference=reference.strip() if reference else None, source_module=source_module, source_entity=source_entity, source_id=source_id, created_by=user_id, status="draft")
        for number, (payload, posting_line) in enumerate(zip(lines, posting_lines), start=1):
            entry.lines.append(JournalEntryLine(tenant_id=tenant_id, company_id=company_id, line_number=number, account_combination_id=posting_line.account_combination_id, department_id=posting_line.department_id, cost_center_id=posting_line.cost_center_id, description=payload.get("description"), reference=payload.get("reference"), debit=posting_line.debit, credit=posting_line.credit, currency_code=currency_code.upper(), exchange_rate=exchange_rate, base_debit=posting_line.debit * exchange_rate, base_credit=posting_line.credit * exchange_rate))
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
        if entry.submitted_by is not None and entry.submitted_by == user_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="The user who submitted the journal entry cannot approve it")
        entry.status = "approved"; entry.approved_by = user_id; entry.approved_at = datetime.now(timezone.utc)
        db.flush()
        if commit:
            db.commit(); db.refresh(entry)
        return entry

    def post(self, db: Session, *, tenant_id: int, entry_id: int, user_id: int, commit: bool = True) -> JournalEntry:
        entry = self._locked_entry(db, tenant_id, entry_id)
        if entry.status not in {"approved", "pending"}:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only approved or pending entries can be posted")
        company_requires_approval = get_company_setting(
            db, entry.company_id, "accounting.require_journal_approval"
        ) is True
        if entry.status == "pending" and (entry.journal.requires_approval or company_requires_approval):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Journal approval is required before posting")
        if entry.status == "approved" and entry.approved_by is not None and entry.approved_by == user_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="The user who approved the journal entry cannot post it")
        period = fiscal_year_repository.get_period_by_id(db, entry.period_id, tenant_id, for_update=True)
        if period is None or period.company_id != entry.company_id or period.fiscal_year_id != entry.fiscal_year_id or period.status != "open" or not period.allow_posting:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Accounting period is not open for posting")
        if not (period.start_date <= entry.entry_date <= period.end_date):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Entry date is outside the posting period")

        db_lines = db.scalars(
            select(JournalEntryLine)
            .where(
                JournalEntryLine.tenant_id == tenant_id,
                JournalEntryLine.company_id == entry.company_id,
                JournalEntryLine.entry_id == entry.id,
            )
            .order_by(JournalEntryLine.line_number)
        ).all()
        try:
            debit, credit = validate_balanced([
                PostingLine(
                    account_combination_id=line.account_combination_id,
                    debit=Decimal(str(line.debit or 0)),
                    credit=Decimal(str(line.credit or 0)),
                    department_id=line.department_id,
                    cost_center_id=line.cost_center_id,
                )
                for line in db_lines
            ])
        except PostingValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc
        entry.total_debit = debit
        entry.total_credit = credit
        entry.status = "posted"; entry.posting_date = entry.entry_date; entry.posted_by = user_id; entry.posted_at = datetime.now(timezone.utc)
        db.flush()
        if commit:
            db.commit(); db.refresh(entry)
        return entry

    def reverse(self, db: Session, *, tenant_id: int, entry_id: int, user_id: int, reversal_date: date | None = None, description: str | None = None, reason: str | None = None) -> JournalEntry:
        """Create and atomically post a balanced reversal for a posted entry."""
        original = self._locked_entry(db, tenant_id, entry_id)
        if original.status != "posted":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only posted entries can be reversed")
        if original.reversal_entry_id is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Journal entry has already been reversed")
        if original.posted_by is not None and original.posted_by == user_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="The user who posted the journal entry cannot reverse it")
        if not reason or not reason.strip():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="A reversal reason is required")

        target_date = reversal_date or date.today()

        # A reversal is a new accounting event. Its posting period must be
        # resolved from the reversal date, not inherited from the original
        # entry. This is essential when an entry is reversed after month/year
        # close or in a later open fiscal period.
        period = fiscal_year_repository.get_period_for_date(
            db=db,
            tenant_id=tenant_id,
            company_id=original.company_id,
            posting_date=target_date,
        )
        if period is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No open accounting period is available for the reversal date",
            )
        period = fiscal_year_repository.get_period_by_id(
            db,
            period.id,
            tenant_id,
            for_update=True,
        )
        if period is None or period.status != "open" or not period.allow_posting:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Accounting period is not open for reversal posting",
            )

        lines = db.scalars(
            select(JournalEntryLine)
            .where(
                JournalEntryLine.tenant_id == tenant_id,
                JournalEntryLine.company_id == original.company_id,
                JournalEntryLine.entry_id == original.id,
            )
            .order_by(JournalEntryLine.line_number)
            .with_for_update()
        ).all()
        if not lines:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Posted journal entry has no lines to reverse")

        reversal = JournalEntry(
            tenant_id=tenant_id,
            company_id=original.company_id,
            branch_id=original.branch_id,
            journal_id=original.journal_id,
            fiscal_year_id=period.fiscal_year_id,
            period_id=period.id,
            reversal_of_id=original.id,
            entry_number=f"REV-{original.entry_number}",
            entry_date=target_date,
            posting_date=target_date,
            reference=original.entry_number,
            description=description or f"Reversal of {original.entry_number}: {reason.strip()}",
            currency_code=original.currency_code,
            exchange_rate=original.exchange_rate,
            source_module="journal_reversal",
            source_entity="journal_entry",
            source_id=original.id,
            created_by=user_id,
            approved_by=user_id,
            approved_at=datetime.now(timezone.utc),
            posted_by=user_id,
            posted_at=datetime.now(timezone.utc),
            status="posted",
        )
        try:
            reversed_payload = reversal_lines([
                PostingLine(
                    account_combination_id=line.account_combination_id,
                    debit=Decimal(str(line.debit or 0)),
                    credit=Decimal(str(line.credit or 0)),
                    department_id=line.department_id,
                    cost_center_id=line.cost_center_id,
                )
                for line in lines
            ])
            debit, credit = validate_balanced(reversed_payload)
        except PostingValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc
        for number, (line, reversed_line) in enumerate(zip(lines, reversed_payload), start=1):
            reversal.lines.append(JournalEntryLine(
                tenant_id=tenant_id,
                company_id=original.company_id,
                line_number=number,
                account_combination_id=reversed_line.account_combination_id,
                department_id=reversed_line.department_id,
                cost_center_id=reversed_line.cost_center_id,
                description=f"Reversal: {line.description}" if line.description else "Reversal",
                reference=original.entry_number,
                debit=reversed_line.debit,
                credit=reversed_line.credit,
                currency_code=line.currency_code,
                exchange_rate=line.exchange_rate,
                base_debit=Decimal(str(line.base_credit or 0)),
                base_credit=Decimal(str(line.base_debit or 0)),
            ))
        reversal.total_debit = debit
        reversal.total_credit = credit
        db.add(reversal)
        db.flush()
        original.reversal_entry_id = reversal.id
        original.status = "reversed"
        db.flush()
        db.commit()
        db.refresh(reversal)
        return reversal

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
