"""IFRS-oriented financial reporting over the canonical journal ledger."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.modules.accounting.chart_of_accounts.models import AccountCombination
from app.modules.accounting.journals.models import JournalEntry, JournalEntryLine


ZERO = Decimal("0")


def _amount(line: JournalEntryLine) -> Decimal:
    return Decimal(str(line.base_debit or 0)) - Decimal(str(line.base_credit or 0))


def _balance(line: JournalEntryLine) -> Decimal:
    account = line.account_combination.natural_account
    signed = _amount(line)
    return signed if account.normal_balance == "debit" else -signed


class FinancialReportingService:
    def _posted_lines(self, db: Session, *, tenant_id: int, company_id: int, start_date: date | None = None, end_date: date | None = None):
        stmt = (
            select(JournalEntryLine)
            .join(JournalEntry, JournalEntry.id == JournalEntryLine.entry_id)
            .options(joinedload(JournalEntryLine.account_combination).joinedload(AccountCombination.natural_account))
            .where(
                JournalEntryLine.tenant_id == tenant_id,
                JournalEntry.company_id == company_id,
                JournalEntry.status == "posted",
            )
        )
        if start_date is not None:
            stmt = stmt.where(JournalEntry.entry_date >= start_date)
        if end_date is not None:
            stmt = stmt.where(JournalEntry.entry_date <= end_date)
        return list(db.scalars(stmt).all())

    def trial_balance(self, db: Session, *, tenant_id: int, company_id: int, as_of: date) -> dict[str, Any]:
        rows: dict[int, dict[str, Any]] = {}
        lines = self._posted_lines(db, tenant_id=tenant_id, company_id=company_id, end_date=as_of)
        for line in lines:
            account = line.account_combination
            natural = account.natural_account
            row = rows.setdefault(account.id, {"account_id": account.id, "code": account.code, "name": account.name_en or account.name_ar, "normal_balance": natural.normal_balance, "debit": ZERO, "credit": ZERO, "balance": ZERO})
            row["debit"] += Decimal(str(line.base_debit or 0))
            row["credit"] += Decimal(str(line.base_credit or 0))
            row["balance"] = row["debit"] - row["credit"] if natural.normal_balance == "debit" else row["credit"] - row["debit"]
        totals = {"debit": sum((r["debit"] for r in rows.values()), ZERO), "credit": sum((r["credit"] for r in rows.values()), ZERO)}
        totals["difference"] = totals["debit"] - totals["credit"]
        return {"as_of": as_of, "rows": sorted(rows.values(), key=lambda r: r["code"]), "totals": totals}

    def profit_and_loss(self, db: Session, *, tenant_id: int, company_id: int, start_date: date, end_date: date) -> dict[str, Any]:
        lines = self._posted_lines(db, tenant_id=tenant_id, company_id=company_id, start_date=start_date, end_date=end_date)
        rows: dict[int, dict[str, Any]] = {}
        for line in lines:
            natural = line.account_combination.natural_account
            if natural.financial_statement != "profit_and_loss":
                continue
            signed = _balance(line)
            row = rows.setdefault(natural.id, {"natural_account_id": natural.id, "code": natural.code, "name": natural.name_en or natural.name_ar, "category": natural.account_category, "amount": ZERO})
            row["amount"] += signed
        total_revenue = sum((r["amount"] for r in rows.values() if r["category"] in {"revenue", "income"}), ZERO)
        total_expense = sum((r["amount"] for r in rows.values() if r["category"] in {"expense", "cost"}), ZERO)
        return {"start_date": start_date, "end_date": end_date, "rows": sorted(rows.values(), key=lambda r: r["code"]), "revenue": total_revenue, "expenses": total_expense, "profit_before_tax": total_revenue - total_expense}

    def statement_of_financial_position(self, db: Session, *, tenant_id: int, company_id: int, as_of: date) -> dict[str, Any]:
        lines = self._posted_lines(db, tenant_id=tenant_id, company_id=company_id, end_date=as_of)
        rows: dict[int, dict[str, Any]] = {}
        for line in lines:
            natural = line.account_combination.natural_account
            if natural.financial_statement != "balance_sheet":
                continue
            row = rows.setdefault(natural.id, {"natural_account_id": natural.id, "code": natural.code, "name": natural.name_en or natural.name_ar, "category": natural.account_category, "amount": ZERO})
            row["amount"] += _balance(line)
        assets = sum((r["amount"] for r in rows.values() if r["category"] == "asset"), ZERO)
        liabilities = sum((r["amount"] for r in rows.values() if r["category"] == "liability"), ZERO)
        equity = sum((r["amount"] for r in rows.values() if r["category"] == "equity"), ZERO)
        return {"as_of": as_of, "rows": sorted(rows.values(), key=lambda r: r["code"]), "assets": assets, "liabilities": liabilities, "equity": equity, "balance_check": assets - liabilities - equity}

    def budget_vs_actual(self, db: Session, *, tenant_id: int, company_id: int, start_date: date, end_date: date, budget_by_account: dict[int, Decimal]) -> list[dict[str, Any]]:
        actuals: dict[int, Decimal] = {}
        for line in self._posted_lines(db, tenant_id=tenant_id, company_id=company_id, start_date=start_date, end_date=end_date):
            natural_id = line.account_combination.natural_account_id
            actuals[natural_id] = actuals.get(natural_id, ZERO) + _balance(line)
        account_ids = set(budget_by_account) | set(actuals)
        return [{"account_id": account_id, "budget": Decimal(budget_by_account.get(account_id, ZERO)), "actual": Decimal(actuals.get(account_id, ZERO)), "variance": Decimal(actuals.get(account_id, ZERO)) - Decimal(budget_by_account.get(account_id, ZERO))} for account_id in sorted(account_ids)]


financial_reporting_service = FinancialReportingService()
