from decimal import Decimal

from app.modules.accounting.reports.schemas import FinancialSummaryResponse, TrialBalanceRow


def test_trial_balance_row_contract():
    row = TrialBalanceRow(
        account_combination_id=1,
        account_code="01001001",
        account_name="Cash",
        financial_statement="balance_sheet",
        account_category="asset",
        normal_balance="debit",
        debit=Decimal("150"),
        credit=Decimal("50"),
        balance=Decimal("100"),
    )
    assert row.balance == Decimal("100")


def test_financial_summary_contract():
    summary = FinancialSummaryResponse(
        company_id=1,
        revenue=Decimal("1000"),
        expenses=Decimal("700"),
        net_profit=Decimal("300"),
        assets=Decimal("5000"),
        liabilities=Decimal("2500"),
        equity=Decimal("2500"),
    )
    assert summary.net_profit == summary.revenue - summary.expenses
