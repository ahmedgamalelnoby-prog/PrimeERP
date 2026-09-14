from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.modules.saas import entitlements


class ScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar(self, *_args, **_kwargs):
        return self.value


class FakeDB:
    def __init__(self, subscription):
        self.subscription = subscription

    def scalar(self, statement):
        sql = str(statement)
        if "subscriptions" in sql:
            return self.subscription
        return None

    def get(self, model, ident):
        return self.subscription.plan if self.subscription else None


def subscription(*, ends_at):
    return SimpleNamespace(
        id=1,
        plan_id=10,
        starts_at=datetime.now(timezone.utc) - timedelta(days=1),
        ends_at=ends_at,
        status="trialing",
        plan=SimpleNamespace(max_users=5, max_companies=1, max_branches=1, max_products=100),
    )


def test_expired_subscription_has_no_core_module_access(monkeypatch):
    expired = subscription(ends_at=datetime.now(timezone.utc) - timedelta(seconds=1))
    monkeypatch.setattr(entitlements, "_active_subscription", lambda db, tenant_id: None)
    db = FakeDB(expired)

    assert entitlements.tenant_has_module(db, 1, "dashboard") is False
    assert entitlements.tenant_has_module(db, 1, "users") is False


def test_expired_subscription_cannot_bypass_resource_limit(monkeypatch):
    monkeypatch.setattr(entitlements, "_active_subscription", lambda db, tenant_id: None)
    db = FakeDB(None)

    with pytest.raises(Exception) as exc:
        entitlements.enforce_user_limit(db, 1)

    assert getattr(exc.value, "status_code", None) == 403


def test_active_subscription_keeps_core_module_access(monkeypatch):
    active = subscription(ends_at=datetime.now(timezone.utc) + timedelta(days=1))
    monkeypatch.setattr(entitlements, "_active_subscription", lambda db, tenant_id: active)
    db = FakeDB(active)

    assert entitlements.tenant_has_module(db, 1, "dashboard") is True
