from decimal import Decimal
from types import SimpleNamespace

from app.modules.accounting.financial_reporting_service import FinancialReportingService


def line(account_id, code, name, statement, category, normal, debit, credit):
    natural = SimpleNamespace(id=account_id, code=code, name_en=name, name_ar=name, financial_statement=statement, account_category=category, normal_balance=normal)
    account = SimpleNamespace(id=account_id, code=code, name_en=name, name_ar=name, natural_account=natural, natural_account_id=account_id)
    return SimpleNamespace(account_combination=account, base_debit=Decimal(debit), base_credit=Decimal(credit))


def test_profit_and_loss_and_balance_sheet_reconcile(monkeypatch):
    service = FinancialReportingService()
    rows = [
        line(1, "400", "Revenue", "profit_and_loss", "revenue", "credit", "0", "1000"),
        line(2, "500", "Expense", "profit_and_loss", "expense", "debit", "600", "0"),
        line(3, "100", "Cash", "balance_sheet", "asset", "debit", "400", "0"),
        line(4, "300", "Equity", "balance_sheet", "equity", "credit", "0", "400"),
    ]
    monkeypatch.setattr(service, "_posted_lines", lambda *args, **kwargs: rows)
    pnl = service.profit_and_loss(None, tenant_id=1, company_id=1, start_date=None, end_date=None)
    assert pnl["revenue"] == Decimal("1000")
    assert pnl["expenses"] == Decimal("600")
    assert pnl["profit_before_tax"] == Decimal("400")
    bs = service.statement_of_financial_position(None, tenant_id=1, company_id=1, as_of=None)
    assert bs["assets"] == Decimal("400")
    assert bs["equity"] == Decimal("400")
    assert bs["balance_check"] == Decimal("0")


def test_budget_vs_actual_variance(monkeypatch):
    service = FinancialReportingService()
    rows = [line(2, "500", "Expense", "profit_and_loss", "expense", "debit", "650", "0")]
    monkeypatch.setattr(service, "_posted_lines", lambda *args, **kwargs: rows)
    result = service.budget_vs_actual(None, tenant_id=1, company_id=1, start_date=None, end_date=None, budget_by_account={2: Decimal("600")})
    assert result == [{"account_id": 2, "budget": Decimal("600"), "actual": Decimal("650"), "variance": Decimal("50")}]
