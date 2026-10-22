import pytest
from pydantic import ValidationError

from app.modules.enterprise.router import PayrollSubmit


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
