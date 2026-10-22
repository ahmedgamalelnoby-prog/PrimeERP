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


def test_integration_worker_checks_later_candidates_without_holding_prior_row_locks(monkeypatch):
    from types import SimpleNamespace
    from app.modules.integrations import worker

    first = SimpleNamespace(id=1, company_id=10, provider="salla", is_active=True, last_sync_at=None)
    second = SimpleNamespace(id=2, company_id=20, provider="salla", is_active=True, last_sync_at=None)

    class Rows:
        def all(self):
            return [1, 2]

    class FakeDB:
        def __init__(self):
            self.scalar_calls = 0
            self.rollbacks = 0
            self.commits = 0

        def scalars(self, _statement):
            return Rows()

        def scalar(self, _statement):
            self.scalar_calls += 1
            return first if self.scalar_calls == 1 else second

        def rollback(self):
            self.rollbacks += 1

        def commit(self):
            self.commits += 1

        def refresh(self, _row):
            pass

    db = FakeDB()
    monkeypatch.setattr(
        worker,
        "integration_sync_due",
        lambda _db, company_id, *_args, **_kwargs: company_id == 20,
    )
    claimed = worker.claim_due_connection(
        db, now=datetime(2026, 10, 22, 10, 0, tzinfo=timezone.utc)
    )
    assert claimed is second
    assert db.scalar_calls == 2
    assert db.rollbacks == 1
    assert db.commits == 1


def test_company_clock_uses_server_time_and_company_timezone():
    from app.modules.company_settings.consumers.general import company_clock_payload

    now = datetime(2026, 10, 21, 16, 30, tzinfo=timezone.utc)
    result = company_clock_payload(now, "Asia/Tokyo")
    assert result["server_time_utc"] == "2026-10-21T16:30:00+00:00"
    assert result["company_timezone"] == "Asia/Tokyo"
    assert result["company_date"] == "2026-10-22"


def test_company_clock_rejects_naive_or_invalid_timezone():
    from app.modules.company_settings.consumers.general import company_clock_payload

    with pytest.raises(ValueError, match="timezone-aware"):
        company_clock_payload(datetime(2026, 10, 21, 16, 30), "UTC")
    with pytest.raises(ValueError, match="Invalid company timezone"):
        company_clock_payload(datetime(2026, 10, 21, 16, 30, tzinfo=timezone.utc), "Invalid/Timezone")


def test_company_clock_endpoint_uses_company_timezone_policy(monkeypatch):
    from types import SimpleNamespace
    from app.modules.company_settings import router as settings_router

    company = SimpleNamespace(id=7, tenant_id=3, name="Test company")
    monkeypatch.setattr(settings_router, "_company", lambda db, company_id, user: company)
    monkeypatch.setattr(settings_router, "policy", lambda db, company_id, key: "Asia/Tokyo")
    now = datetime(2026, 10, 21, 16, 30, tzinfo=timezone.utc)
    monkeypatch.setattr(settings_router, "company_clock_payload", lambda value, tz: {
        "server_time_utc": value.isoformat(), "company_timezone": tz, "company_date": "2026-10-22"
    })

    result = settings_router.get_company_clock(company_id=7, db=object(), user=object())

    assert result == {
        "company_id": 7,
        "server_time_utc": now.isoformat(),
        "company_timezone": "Asia/Tokyo",
        "company_date": "2026-10-22",
    }


@pytest.mark.parametrize("configured_format", ["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"])
def test_company_date_format_endpoint_returns_validated_policy(monkeypatch, configured_format):
    from types import SimpleNamespace
    from app.modules.company_settings import router as settings_router

    company = SimpleNamespace(id=12, tenant_id=3, name="Test company")
    monkeypatch.setattr(settings_router, "_company", lambda db, company_id, user: company)
    monkeypatch.setattr(settings_router, "policy", lambda db, company_id, key: configured_format)

    result = settings_router.get_company_date_format(company_id=12, db=object(), user=object())

    assert result == {"company_id": 12, "date_format": configured_format}


def test_company_date_format_endpoint_rejects_invalid_stored_policy(monkeypatch):
    from types import SimpleNamespace
    from fastapi import HTTPException
    from app.modules.company_settings import router as settings_router

    company = SimpleNamespace(id=12, tenant_id=3, name="Test company")
    monkeypatch.setattr(settings_router, "_company", lambda db, company_id, user: company)
    monkeypatch.setattr(settings_router, "policy", lambda db, company_id, key: "invalid")

    with pytest.raises(HTTPException) as exc:
        settings_router.get_company_date_format(company_id=12, db=object(), user=object())

    assert exc.value.status_code == 500
