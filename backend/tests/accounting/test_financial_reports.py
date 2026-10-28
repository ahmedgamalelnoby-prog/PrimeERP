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



def test_financial_summary_uses_period_activity_and_cumulative_balance_sheet(monkeypatch):
    service = FinancialReportService()
    calls = []

    def fake_trial_balance(db, *, tenant_id, company_id, from_date=None, to_date=None):
        calls.append((from_date, to_date))
        if from_date is not None:
            rows = [
                SimpleNamespace(financial_statement="profit_and_loss", account_category="revenue", normal_balance="credit", balance=Decimal("100")),
                SimpleNamespace(financial_statement="profit_and_loss", account_category="expense", normal_balance="debit", balance=Decimal("40")),
            ]
        else:
            rows = [
                SimpleNamespace(financial_statement="balance_sheet", account_category="asset", normal_balance="debit", balance=Decimal("300")),
                SimpleNamespace(financial_statement="balance_sheet", account_category="liability", normal_balance="credit", balance=Decimal("100")),
                SimpleNamespace(financial_statement="balance_sheet", account_category="equity", normal_balance="credit", balance=Decimal("200")),
            ]
        return SimpleNamespace(rows=rows)

    monkeypatch.setattr(service, "trial_balance", fake_trial_balance)
    summary = service.financial_summary(
        None,
        tenant_id=12,
        company_id=99,
        from_date=__import__("datetime").date(2026, 1, 1),
        to_date=__import__("datetime").date(2026, 1, 31),
    )

    assert summary.revenue == Decimal("100")
    assert summary.expenses == Decimal("40")
    assert summary.net_profit == Decimal("60")
    assert summary.assets == Decimal("300")
    assert summary.liabilities == Decimal("100")
    assert summary.equity == Decimal("200")
    assert calls == [
        (__import__("datetime").date(2026, 1, 1), __import__("datetime").date(2026, 1, 31)),
        (None, __import__("datetime").date(2026, 1, 31)),
    ]
