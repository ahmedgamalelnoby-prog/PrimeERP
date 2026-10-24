import pytest
from datetime import date
from pydantic import ValidationError

from app.modules.enterprise.router import PayrollPost, PayrollSubmit


def test_payroll_submit_accepts_distinct_positive_approvers():
    payload = PayrollSubmit(approver_ids=[7, 12])
    assert payload.approver_ids == [7, 12]


def test_payroll_submit_rejects_duplicate_approvers():
    with pytest.raises(ValidationError, match="unique"):
        PayrollSubmit(approver_ids=[7, 7])


@pytest.mark.parametrize("approver_ids", [[0], [-3], [1, 0]])
def test_payroll_submit_rejects_non_positive_approver_ids(approver_ids):
    with pytest.raises(ValidationError, match="positive integers"):
        PayrollSubmit(approver_ids=approver_ids)


def test_payroll_submit_allows_empty_list_before_policy_is_checked():
    # Whether approvers are required depends on the company's runtime policy;
    # the endpoint enforces that condition when the payroll run is submitted.
    assert PayrollSubmit().approver_ids == []


def test_payroll_post_requires_explicit_accounting_mapping():
    payload = PayrollPost(
        branch_id=1, journal_id=2, fiscal_year_id=3, period_id=4,
        entry_date=date(2026, 10, 1), salary_expense_account_id=5,
        deductions_payable_account_id=6, net_payable_account_id=7,
    )
    assert payload.salary_expense_account_id == 5


def test_payroll_post_rejects_zero_account_id():
    with pytest.raises(ValidationError):
        PayrollPost(
            branch_id=1, journal_id=2, fiscal_year_id=3, period_id=4,
            entry_date=date(2026, 10, 1), salary_expense_account_id=0,
            deductions_payable_account_id=6, net_payable_account_id=7,
        )
