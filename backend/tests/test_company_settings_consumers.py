from datetime import datetime, timedelta, timezone

import pytest

from app.modules.company_settings.registry import validate_value

from app.modules.company_settings.consumers.approvals import approval_escalation_due, approval_plan
from app.modules.company_settings.consumers.general import format_company_date
from app.modules.company_settings.consumers.hr import attendance_source_allowed, biometric_sync_due
from app.modules.company_settings.consumers.integrations import integration_sync_due
from app.modules.company_settings.consumers.pos import cash_drawer_open_allowed


class FakeDB:
    def __init__(self, values):
        self.values = values


def _patch_policy(monkeypatch, module, values):
    monkeypatch.setattr(module, "policy", lambda db, company_id, key: values[key])
    monkeypatch.setattr(module, "require_policy_bool", lambda db, company_id, key: values[key])
    monkeypatch.setattr(module, "require_policy_int", lambda db, company_id, key, minimum=0: values[key])


def test_date_format_policy(monkeypatch):
    from app.modules.company_settings.consumers import general
    monkeypatch.setattr(general, "policy", lambda db, company_id, key: "YYYY-MM-DD")
    assert format_company_date(FakeDB({}), 1, datetime(2026, 10, 22)) == "2026-10-22"


def test_date_format_rejects_unknown_value(monkeypatch):
    from app.modules.company_settings.consumers import general
    monkeypatch.setattr(general, "policy", lambda db, company_id, key: "invalid")
    with pytest.raises(ValueError):
        format_company_date(FakeDB({}), 1, datetime(2026, 10, 22))


def test_attendance_source_policy(monkeypatch):
    from app.modules.company_settings.consumers import hr
    monkeypatch.setattr(hr, "policy", lambda db, company_id, key: "biometric")
    assert attendance_source_allowed(FakeDB({}), 1, "Biometric")
    assert not attendance_source_allowed(FakeDB({}), 1, "manual")


def test_biometric_sync_interval(monkeypatch):
    from app.modules.company_settings.consumers import hr
    monkeypatch.setattr(hr, "require_policy_int", lambda db, company_id, key, minimum=0: 15)
    now = datetime(2026, 10, 22, 10, 15, tzinfo=timezone.utc)
    assert biometric_sync_due(FakeDB({}), 1, now - timedelta(minutes=15), now=now)
    assert not biometric_sync_due(FakeDB({}), 1, now - timedelta(minutes=14), now=now)
    assert biometric_sync_due(FakeDB({}), 1, None, now=now)


def test_approval_plan_modes():
    assert approval_plan("sequential", [4, 5, 5]) == {
        "mode": "sequential", "approver_ids": [4, 5], "required_approvals": 2, "sequential": True
    }
    assert approval_plan("parallel", [4, 5])["required_approvals"] == 2
    assert approval_plan("any_one", [4, 5])["required_approvals"] == 1
    with pytest.raises(ValueError):
        approval_plan("unknown", [4])


def test_approval_escalation_threshold(monkeypatch):
    from app.modules.company_settings.consumers import approvals
    monkeypatch.setattr(approvals, "require_policy_int", lambda db, company_id, key, minimum=0: 24)
    created = datetime(2026, 10, 21, 10, tzinfo=timezone.utc)
    assert approval_escalation_due(FakeDB({}), 1, created, now=created + timedelta(hours=24))
    assert not approval_escalation_due(FakeDB({}), 1, created, now=created + timedelta(hours=23))


def test_cash_drawer_policy(monkeypatch):
    from app.modules.company_settings.consumers import pos
    monkeypatch.setattr(pos, "require_policy_bool", lambda db, company_id, key: False)
    assert cash_drawer_open_allowed(FakeDB({}), 1, linked_to_transaction=True)
    assert not cash_drawer_open_allowed(FakeDB({}), 1, linked_to_transaction=False)


def test_automatic_integration_sync_disabled(monkeypatch):
    from app.modules.company_settings.consumers import integrations
    monkeypatch.setattr(integrations, "require_policy_bool", lambda db, company_id, key: False)
    assert not integration_sync_due(FakeDB({}), 1, None, interval_minutes=15)



@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("hr.biometric_sync_interval_minutes", 0),
        ("workflow.escalation_after_hours", 0),
    ],
)
def test_company_policy_intervals_must_be_positive(key, value):
    with pytest.raises(ValueError, match="must be at least 1"):
        validate_value(key, value)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("hr.biometric_sync_interval_minutes", 1),
        ("workflow.escalation_after_hours", 1),
    ],
)
def test_company_policy_intervals_accept_positive_values(key, value):
    assert validate_value(key, value) == value



def test_automatic_integration_sync_worker_skips_when_policy_is_disabled(monkeypatch):
    from types import SimpleNamespace
    from app.modules.integrations import worker

    class Rows:
        def all(self):
            return [SimpleNamespace(
                id=9, company_id=4, provider="salla", is_active=True, last_sync_at=None
            )]

    class FakeDB:
        def scalars(self, _statement):
            return Rows()

        def rollback(self):
            self.rolled_back = True

        def close(self):
            pass

    db = FakeDB()
    monkeypatch.setattr(worker, "integration_sync_due", lambda *args, **kwargs: False)
    result = worker.run_once(lambda: db)
    assert result == {"claimed": 0, "succeeded": 0, "failed": 0}
    assert getattr(db, "rolled_back", False)


def test_automatic_integration_sync_worker_runs_a_claimed_connection(monkeypatch):
    from types import SimpleNamespace
    from app.modules.integrations import worker

    connection = SimpleNamespace(
        id=9, company_id=4, provider="salla", is_active=True, last_sync_at=None
    )

    class Rows:
        def all(self):
            return [connection]

    class FakeDB:
        def __init__(self):
            self.committed = False

        def scalars(self, _statement):
            return Rows()

        def scalar(self, _statement):
            return connection

        def commit(self):
            self.committed = True

        def refresh(self, _row):
            pass

        def rollback(self):
            pass

        def close(self):
            pass

    sessions = [FakeDB(), FakeDB()]
    monkeypatch.setattr(worker, "integration_sync_due", lambda *args, **kwargs: True)
    monkeypatch.setattr(worker, "full_sync", lambda db, connection_id: {"ok": connection_id})
    result = worker.run_once(lambda: sessions.pop(0))
    assert result == {"claimed": 1, "succeeded": 1, "failed": 0}
