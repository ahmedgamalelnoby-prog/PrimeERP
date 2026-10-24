from datetime import datetime, timedelta, timezone

import pytest

from app.modules.company_settings.consumers import approvals, hr, pos


def test_attendance_source_allows_only_the_configured_source(monkeypatch):
    monkeypatch.setattr(hr, "policy", lambda db, company_id, key: "biometric")
    assert hr.attendance_source_allowed(None, 7, "biometric") is True
    assert hr.attendance_source_allowed(None, 7, " BIOMETRIC ") is True
    assert hr.attendance_source_allowed(None, 7, "manual") is False


def test_biometric_sync_due_uses_company_interval_and_normalizes_naive_datetimes(monkeypatch):
    monkeypatch.setattr(hr, "require_policy_int", lambda db, company_id, key, minimum: 15)
    now = datetime(2026, 10, 24, 12, 15, tzinfo=timezone.utc)
    assert hr.biometric_sync_due(None, 7, None, now=now) is True
    assert hr.biometric_sync_due(
        None, 7, datetime(2026, 10, 24, 12, 0), now=now
    ) is True
    assert hr.biometric_sync_due(
        None, 7, datetime(2026, 10, 24, 12, 1, tzinfo=timezone.utc), now=now
    ) is False


@pytest.mark.parametrize(
    ("mode", "required", "sequential"),
    [("sequential", 3, True), ("parallel", 3, False), ("any_one", 1, False)],
)
def test_approval_plan_encodes_mode_semantics(mode, required, sequential):
    plan = approvals.approval_plan(mode, [4, 5, 6, 5])
    assert plan == {
        "mode": mode,
        "approver_ids": [4, 5, 6],
        "required_approvals": required,
        "sequential": sequential,
    }


def test_approval_plan_rejects_empty_or_invalid_approvers():
    with pytest.raises(ValueError, match="At least one approver"):
        approvals.approval_plan("parallel", [])
    with pytest.raises(ValueError, match="positive integers"):
        approvals.approval_plan("sequential", [1, 0])


def test_approval_escalation_uses_configured_sla(monkeypatch):
    monkeypatch.setattr(
        approvals, "require_policy_int", lambda db, company_id, key, minimum: 24
    )
    created = datetime(2026, 10, 23, 12, 0, tzinfo=timezone.utc)
    assert approvals.approval_escalation_due(
        None, 7, created, now=created + timedelta(hours=24)
    ) is True
    assert approvals.approval_escalation_due(
        None, 7, created, now=created + timedelta(hours=23, minutes=59)
    ) is False


def test_cash_drawer_policy_only_gates_unlinked_openings(monkeypatch):
    monkeypatch.setattr(
        pos, "require_policy_bool", lambda db, company_id, key: False
    )
    assert pos.cash_drawer_open_allowed(None, 7, linked_to_transaction=True) is True
    assert pos.cash_drawer_open_allowed(None, 7, linked_to_transaction=False) is False
    monkeypatch.setattr(
        pos, "require_policy_bool", lambda db, company_id, key: True
    )
    assert pos.cash_drawer_open_allowed(None, 7, linked_to_transaction=False) is True
