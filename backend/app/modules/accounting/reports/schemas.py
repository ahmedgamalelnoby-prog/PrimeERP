from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class TrialBalanceRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_combination_id: int
    account_code: str
    account_name: str
    financial_statement: str
    account_category: str
    normal_balance: str
    debit: Decimal
    credit: Decimal
    balance: Decimal


class TrialBalanceResponse(BaseModel):
    company_id: int
    from_date: str | None
    to_date: str | None
    rows: list[TrialBalanceRow]
    total_debit: Decimal
    total_credit: Decimal


class FinancialSummaryResponse(BaseModel):
    company_id: int
    revenue: Decimal
    expenses: Decimal
    net_profit: Decimal
    assets: Decimal
    liabilities: Decimal
    equity: Decimal
