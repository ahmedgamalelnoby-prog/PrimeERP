from decimal import Decimal

from app.modules.accounting.chart_of_accounts.models import AccountingCostCenter
from app.modules.accounting.ifrs_cma_models import (
    AccountingPolicy,
    ChartOfAccount,
    CostCenter,
    FiscalPeriod,
    JournalEntry,
    JournalLine,
    ManagementBudget,
    ManagementBudgetLine,
)
from app.modules.accounting.ifrs_cma_service import IFRSCMAService


def test_ifrs_cma_models_and_controls_exist():
    assert AccountingPolicy.__tablename__ == "accounting_policies"
    assert FiscalPeriod.__tablename__ == "accounting_fiscal_periods"
    assert ChartOfAccount.__tablename__ == "accounting_accounts"
    assert JournalEntry.__tablename__ == "accounting_journal_entries"
    assert JournalLine.__tablename__ == "accounting_journal_lines"
    assert CostCenter.__tablename__ == "accounting_cost_centers"
    assert ManagementBudget.__tablename__ == "accounting_management_budgets"
    assert ManagementBudgetLine.__tablename__ == "accounting_management_budget_lines"


def test_ifrs_cma_cost_center_uses_canonical_accounting_mapping():
    assert CostCenter is AccountingCostCenter
    assert CostCenter.__table__ is AccountingCostCenter.__table__


def test_journal_is_strictly_balanced():
    service = IFRSCMAService()
    service.validate_balanced_lines([
        {"debit": Decimal("100"), "credit": Decimal("0")},
        {"debit": Decimal("0"), "credit": Decimal("100")},
    ])


def test_unbalanced_journal_is_rejected():
    service = IFRSCMAService()
    try:
        service.validate_balanced_lines([
            {"debit": Decimal("100"), "credit": Decimal("0")},
            {"debit": Decimal("0"), "credit": Decimal("90")},
        ])
    except ValueError as exc:
        assert "equal" in str(exc).lower()
    else:
        raise AssertionError("Unbalanced journal was accepted")


def test_accounting_policy_defaults_to_egypt_ifrs_cma():
    policy = AccountingPolicy(company_id=1)
    assert policy.jurisdiction == "EG"
    assert policy.accounting_framework == "IFRS"
    assert policy.management_framework == "CMA"
    assert policy.functional_currency == "EGP"
    assert policy.tax_authority == "EGYPT_ETA"


def test_journal_lines_cannot_have_both_sides():
    constraints = {c.name for c in JournalLine.__table__.constraints}
    assert "ck_journal_line_one_side" in constraints
    assert "ck_journal_line_nonzero" in constraints
