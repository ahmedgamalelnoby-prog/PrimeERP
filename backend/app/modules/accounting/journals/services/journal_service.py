from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.accounting.chart_of_accounts.models import AccountCombination, AccountingCostCenter, AccountingDepartment
from app.modules.accounting.fiscal_years.repositories.fiscal_year_repository import fiscal_year_repository
from app.modules.accounting.journals.models import JournalEntry, JournalEntryLine
from app.modules.accounting.journals.repositories.journal_repository import journal_repository
from app.modules.branches.models import Branch
from app.modules.companies.models import Company

_SYSTEM_SOURCE_MODULES = {"commerce", "shipping", "inventory", "purchasing", "sales", "payments", "assets", "payroll"}


class JournalService:
    """Application boundary for journal-entry lifecycle and posting rules."""

    def list_journals(self, db: Session, tenant_id: int, company_id: int):
        self._active_company(db, tenant_id, company_id)
        return journal_repository.list_journals(db, tenant_id, company_id)

    def list_entries(self, db: Session, tenant_id: int, company_id: int, **filters):
        self._active_company(db, tenant_id, company_id)
        return journal_repository.list_entries(db, tenant_id, company_id, **filters)

    def get_entry(self, db: Session, tenant_id: int, entry_id: int) -> JournalEntry:
        entry = journal_repository.get_entry(db, entry_id, tenant_id)
        if entry is None:
            raise HTTPException(status_code=404, detail="Journal entry not found")
        self._active_company(db, tenant_id, entry.company_id)
        return entry

    def create_draft(self, db: Session, *, tenant_id: int, company_id: int, branch_id: int, journal_id: int, fiscal_year_id: int, period_id: int, entry_number: str, entry_date: date, description: str, lines: list[dict], user_id: int | None = None, currency_code: str = "EGP", exchange_rate: Decimal = Decimal("1"), reference: str | None = None, source_module: str | None = None, source_entity: str | None = None, source_id: int | None = None, commit: bool = True) -> JournalEntry:
        self._active_company(db, tenant_id, company_id)
        entry_number = entry_number.strip()
        if not entry_number or not description.strip():
            raise HTTPException(status_code=422, detail="Entry number and journal description are required")
        source_fields = (source_module, source_entity, source_id)
        if any(value is not None for value in source_fields) and not all(value is not None for value in source_fields):
            raise HTTPException(status_code=422, detail="source_module, source_entity and source_id must be supplied together")
        if source_module is not None and source_module not in _SYSTEM_SOURCE_MODULES:
            raise HTTPException(status_code=422, detail="Unsupported accounting source module")
        if db.scalar(select(JournalEntry.id).where(JournalEntry.tenant_id == tenant_id, JournalEntry.entry_number == entry_number)) is not None:
            raise HTTPException(status_code=409, detail="Journal entry number already exists")
        if source_module is not None and db.scalar(select(JournalEntry.id).where(JournalEntry.tenant_id == tenant_id, JournalEntry.company_id == company_id, JournalEntry.source_module == source_module, JournalEntry.source_entity == source_entity, JournalEntry.source_id == source_id)) is not None:
            raise HTTPException(status_code=409, detail="A journal entry already exists for this source transaction")
        journal = journal_repository.get_journal(db, journal_id, tenant_id, company_id)
        if journal is None or not journal.is_active:
            raise HTTPException(status_code=404, detail="Accounting journal not found")
        if not journal.allow_manual_entries and source_module not in _SYSTEM_SOURCE_MODULES:
            raise HTTPException(status_code=409, detail="Manual entries are disabled for this journal")
        if len(lines) < 2:
            raise HTTPException(status_code=422, detail="Journal entry requires at least two lines")
        if exchange_rate <= 0:
            raise HTTPException(status_code=422, detail="Exchange rate must be positive")
        fiscal_year = fiscal_year_repository.get_by_id(db, fiscal_year_id, tenant_id)
        if fiscal_year is None or fiscal_year.company_id != company_id:
            raise HTTPException(status_code=422, detail="Fiscal year does not belong to the selected company")
        period = fiscal_year_repository.get_period_by_id(db, period_id, tenant_id)
        if period is None or period.company_id != company_id or period.fiscal_year_id != fiscal_year_id or not (period.start_date <= entry_date <= period.end_date):
            raise HTTPException(status_code=422, detail="Fiscal period does not belong to the selected company/fiscal year or date")
        branch = db.scalar(select(Branch).where(Branch.id == branch_id, Branch.company_id == company_id, Branch.tenant_id == tenant_id, Branch.is_active.is_(True)))
        if branch is None:
            raise HTTPException(status_code=422, detail="Branch does not belong to the selected company or is inactive")
        account_ids = set()
        department_ids = set()
        cost_center_ids = set()
        for number, payload in enumerate(lines, 1):
            try:
                account_ids.add(int(payload["account_combination_id"]))
                if payload.get("department_id") is not None: department_ids.add(int(payload["department_id"]))
                if payload.get("cost_center_id") is not None: cost_center_ids.add(int(payload["cost_center_id"]))
            except (KeyError, TypeError, ValueError):
                raise HTTPException(status_code=422, detail=f"Invalid accounting dimension on journal line {number}")
        accounts = db.scalars(select(AccountCombination).where(AccountCombination.id.in_(account_ids), AccountCombination.company_id == company_id, AccountCombination.is_active.is_(True))).all()
        if {x.id for x in accounts} != account_ids:
            raise HTTPException(status_code=422, detail="One or more journal accounts do not belong to the selected company or are inactive")
        if department_ids:
            departments = db.scalars(select(AccountingDepartment).where(AccountingDepartment.id.in_(department_ids), AccountingDepartment.company_id == company_id, AccountingDepartment.is_active.is_(True))).all()
            if {x.id for x in departments} != department_ids:
                raise HTTPException(status_code=422, detail="One or more journal departments do not belong to the selected company or are inactive")
        cost_centers = {}
        if cost_center_ids:
            rows = db.scalars(select(AccountingCostCenter).where(AccountingCostCenter.id.in_(cost_center_ids), AccountingCostCenter.company_id == company_id, AccountingCostCenter.is_active.is_(True))).all()
            if {x.id for x in rows} != cost_center_ids:
                raise HTTPException(status_code=422, detail="One or more journal cost centers do not belong to the selected company or are inactive")
            cost_centers = {x.id: x for x in rows}
        debit = Decimal("0"); credit = Decimal("0")
        entry = JournalEntry(tenant_id=tenant_id, company_id=company_id, branch_id=branch_id, journal_id=journal_id, fiscal_year_id=fiscal_year_id, period_id=period_id, entry_number=entry_number, entry_date=entry_date, description=description.strip(), currency_code=currency_code.upper(), exchange_rate=exchange_rate, reference=reference.strip() if reference else None, source_module=source_module, source_entity=source_entity, source_id=source_id, created_by=user_id, status="draft")
        for number, payload in enumerate(lines, 1):
            try:
                line_debit = Decimal(str(payload.get("debit", 0))); line_credit = Decimal(str(payload.get("credit", 0))); account_id = int(payload["account_combination_id"])
            except (KeyError, TypeError, ValueError, InvalidOperation):
                raise HTTPException(status_code=422, detail=f"Invalid account or amount on journal line {number}")
            if not line_debit.is_finite() or not line_credit.is_finite() or line_debit < 0 or line_credit < 0 or (line_debit > 0 and line_credit > 0) or (line_debit == 0 and line_credit == 0):
                raise HTTPException(status_code=422, detail=f"Invalid amount on journal line {number}")
            cc_id = int(payload["cost_center_id"]) if payload.get("cost_center_id") is not None else None
            dep_id = int(payload["department_id"]) if payload.get("department_id") is not None else None
            if cc_id is not None and dep_id is not None and cost_centers[cc_id].department_id is not None and cost_centers[cc_id].department_id != dep_id:
                raise HTTPException(status_code=422, detail=f"Cost center and department mismatch on journal line {number}")
            if cc_id is not None and cost_centers[cc_id].branch_id is not None and cost_centers[cc_id].branch_id != branch_id:
                raise HTTPException(status_code=422, detail=f"Cost center is assigned to another branch on journal line {number}")
            debit += line_debit; credit += line_credit
            entry.lines.append(JournalEntryLine(tenant_id=tenant_id, line_number=number, account_combination_id=account_id, department_id=dep_id, cost_center_id=cc_id, description=payload.get("description"), reference=payload.get("reference"), debit=line_debit, credit=line_credit, currency_code=currency_code.upper(), exchange_rate=exchange_rate, base_debit=line_debit * exchange_rate, base_credit=line_credit * exchange_rate))
        if debit != credit:
            raise HTTPException(status_code=422, detail="Journal entry must be balanced: total debit must equal total credit")
        entry.total_debit = debit; entry.total_credit = credit
        db.add(entry); db.flush()
        if commit: db.commit(); db.refresh(entry)
        return entry

    def submit(self, db: Session, *, tenant_id: int, entry_id: int, user_id: int, commit: bool = True) -> JournalEntry:
        entry = self._locked_entry(db, tenant_id, entry_id)
        if entry.status != "draft": raise HTTPException(409, "Only draft entries can be submitted")
        entry.status = "pending"; entry.submitted_by = user_id; entry.submitted_at = datetime.now(timezone.utc); db.flush()
        if commit: db.commit(); db.refresh(entry)
        return entry

    def approve(self, db: Session, *, tenant_id: int, entry_id: int, user_id: int, commit: bool = True) -> JournalEntry:
        entry = self._locked_entry(db, tenant_id, entry_id)
        if entry.status != "pending": raise HTTPException(409, "Only pending entries can be approved")
        entry.status = "approved"; entry.approved_by = user_id; entry.approved_at = datetime.now(timezone.utc); db.flush()
        if commit: db.commit(); db.refresh(entry)
        return entry

    def post(self, db: Session, *, tenant_id: int, entry_id: int, user_id: int, commit: bool = True) -> JournalEntry:
        entry = self._locked_entry(db, tenant_id, entry_id)
        if entry.status not in {"approved", "pending"}: raise HTTPException(409, "Only approved or pending entries can be posted")
        if entry.status == "pending" and entry.journal.requires_approval: raise HTTPException(409, "Journal approval is required before posting")
        period = fiscal_year_repository.get_period_by_id(db, entry.period_id, tenant_id, for_update=True)
        if period is None or period.company_id != entry.company_id or period.fiscal_year_id != entry.fiscal_year_id or period.status != "open" or not period.allow_posting or not (period.start_date <= entry.entry_date <= period.end_date): raise HTTPException(409, "Accounting period is not open for posting")
        if entry.total_debit != entry.total_credit: raise HTTPException(422, "Cannot post an unbalanced journal entry")
        entry.status = "posted"; entry.posting_date = entry.entry_date; entry.posted_by = user_id; entry.posted_at = datetime.now(timezone.utc); db.flush()
        if commit: db.commit(); db.refresh(entry)
        return entry

    def cancel(self, db: Session, *, tenant_id: int, entry_id: int, user_id: int, commit: bool = True) -> JournalEntry:
        entry = self._locked_entry(db, tenant_id, entry_id)
        if entry.status == "posted": raise HTTPException(409, "Posted entries cannot be cancelled; use a reversal entry")
        if entry.status in {"cancelled", "reversed"}: raise HTTPException(409, "Journal entry is already closed")
        entry.status = "cancelled"; entry.cancelled_by = user_id; entry.cancelled_at = datetime.now(timezone.utc); db.flush()
        if commit: db.commit(); db.refresh(entry)
        return entry

    @staticmethod
    def _active_company(db: Session, tenant_id: int, company_id: int) -> Company:
        company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == tenant_id, Company.is_active.is_(True)))
        if company is None: raise HTTPException(403, "Company is outside the current tenant or inactive")
        return company

    @staticmethod
    def _locked_entry(db: Session, tenant_id: int, entry_id: int) -> JournalEntry:
        entry = journal_repository.get_entry(db, entry_id, tenant_id, for_update=True)
        if entry is None: raise HTTPException(404, "Journal entry not found")
        return entry


journal_service = JournalService()
