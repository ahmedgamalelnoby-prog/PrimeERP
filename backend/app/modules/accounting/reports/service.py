from datetime import date
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.accounting.chart_of_accounts.models import AccountCombination, NaturalAccount
from app.modules.accounting.journals.models import JournalEntry, JournalEntryLine
from app.modules.accounting.reports.schemas import (
    FinancialSummaryResponse,
    TrialBalanceResponse,
    TrialBalanceRow,
)


class FinancialReportService:
    """Read-only reporting boundary over posted journal entries."""

    def trial_balance(
        self,
        db: Session,
        *,
        tenant_id: int,
        company_id: int,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> TrialBalanceResponse:
        query = (
            db.query(
                AccountCombination.id.label("account_combination_id"),
                AccountCombination.code.label("account_code"),
                AccountCombination.name_ar.label("account_name"),
                NaturalAccount.financial_statement.label("financial_statement"),
                NaturalAccount.account_category.label("account_category"),
                NaturalAccount.normal_balance.label("normal_balance"),
                func.coalesce(func.sum(JournalEntryLine.debit), 0).label("debit"),
                func.coalesce(func.sum(JournalEntryLine.credit), 0).label("credit"),
            )
            .join(JournalEntryLine, JournalEntryLine.account_combination_id == AccountCombination.id)
            .join(JournalEntry, JournalEntry.id == JournalEntryLine.entry_id)
            .join(NaturalAccount, NaturalAccount.id == AccountCombination.natural_account_id)
            .filter(
                JournalEntry.tenant_id == tenant_id,
                JournalEntry.company_id == company_id,
                JournalEntry.status == "posted",
            )
            .group_by(
                AccountCombination.id,
                AccountCombination.code,
                AccountCombination.name_ar,
                NaturalAccount.financial_statement,
                NaturalAccount.account_category,
                NaturalAccount.normal_balance,
            )
            .order_by(AccountCombination.code)
        )
        if from_date is not None:
            query = query.filter(JournalEntry.entry_date >= from_date)
        if to_date is not None:
            query = query.filter(JournalEntry.entry_date <= to_date)

        rows: list[TrialBalanceRow] = []
        total_debit = Decimal("0")
        total_credit = Decimal("0")
        for row in query.all():
            debit = Decimal(row.debit or 0)
            credit = Decimal(row.credit or 0)
            balance = debit - credit if row.normal_balance == "debit" else credit - debit
            rows.append(
                TrialBalanceRow(
                    account_combination_id=row.account_combination_id,
                    account_code=row.account_code,
                    account_name=row.account_name,
                    financial_statement=row.financial_statement,
                    account_category=row.account_category,
                    normal_balance=row.normal_balance,
                    debit=debit,
                    credit=credit,
                    balance=balance,
                )
            )
            total_debit += debit
            total_credit += credit

        return TrialBalanceResponse(
            company_id=company_id,
            from_date=from_date.isoformat() if from_date else None,
            to_date=to_date.isoformat() if to_date else None,
            rows=rows,
            total_debit=total_debit,
            total_credit=total_credit,
        )

    def financial_summary(
        self,
        db: Session,
        *,
        tenant_id: int,
        company_id: int,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> FinancialSummaryResponse:
        trial = self.trial_balance(
            db,
            tenant_id=tenant_id,
            company_id=company_id,
            from_date=from_date,
            to_date=to_date,
        )
        revenue = Decimal("0")
        expenses = Decimal("0")
        assets = Decimal("0")
        liabilities = Decimal("0")
        equity = Decimal("0")

        for row in trial.rows:
            if row.financial_statement == "profit_and_loss":
                if row.account_category in {"revenue", "income"} or row.normal_balance == "credit":
                    revenue += row.balance
                else:
                    expenses += row.balance
            elif row.financial_statement == "balance_sheet":
                if row.account_category in {"asset", "assets"} or row.normal_balance == "debit":
                    assets += row.balance
                elif row.account_category in {"liability", "liabilities"}:
                    liabilities += row.balance
                else:
                    equity += row.balance

        return FinancialSummaryResponse(
            company_id=company_id,
            revenue=revenue,
            expenses=expenses,
            net_profit=revenue - expenses,
            assets=assets,
            liabilities=liabilities,
            equity=equity,
        )


financial_report_service = FinancialReportService()
