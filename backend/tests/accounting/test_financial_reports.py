from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.modules.accounting.reports.service import FinancialReportService

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


def test_financial_report_rejects_company_outside_tenant_with_forbidden_status():
    service = FinancialReportService()
    db = SimpleNamespace(scalar=lambda query: None)

    with pytest.raises(HTTPException) as error:
        service._assert_company(db, tenant_id=12, company_id=99)

    assert error.value.status_code == 403
    assert error.value.detail == "Company is outside the current tenant"
