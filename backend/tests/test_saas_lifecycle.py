from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.modules.saas import lifecycle


class _DB:
    def __init__(self, tenant=None, plan=None, current=None):
        self.tenant = tenant
        self.plan = plan
        self.current = current
        self.added = []
        self.commits = 0

    def get(self, model, object_id):
        if model is lifecycle.Tenant:
            return self.tenant
        if model is lifecycle.SubscriptionPlan:
            return self.plan
        return None

    def scalar(self, statement):
        return self.current

    def add(self, value):
        self.added.append(value)

    def commit(self):
        self.commits += 1

    def refresh(self, value):
        return None


def test_convert_trial_to_paid_changes_same_trial_subscription():
    tenant = SimpleNamespace(id=7, status="trial", is_trial=True, is_active=True, trial_ends_at="old")
    plan = SimpleNamespace(id=3, is_active=True)
    subscription = SimpleNamespace(
        id=9,
        tenant_id=7,
        plan_id=1,
        status="trialing",
        billing_cycle="monthly",
        starts_at=None,
        ends_at=None,
        trial_ends_at="old",
        next_billing_date=None,
        cancelled_at=None,
        is_auto_renew=False,
    )
    db = _DB(tenant, plan, subscription)

    result = lifecycle.convert_trial_to_paid(db, 7, 3, "yearly", True)

    assert result is subscription
    assert subscription.plan_id == 3
    assert subscription.status == "active"
    assert subscription.billing_cycle == "yearly"
    assert subscription.is_auto_renew is True
    assert subscription.next_billing_date == subscription.ends_at
    assert tenant.status == "active"
    assert tenant.is_trial is False
    assert tenant.trial_ends_at is None
    assert db.commits == 1


def test_renewal_after_expiry_starts_from_now():
    now = datetime.now(timezone.utc)
    tenant = SimpleNamespace(id=7, status="expired", is_trial=True, is_active=False, suspended_at="x", suspension_reason="x")
    plan = SimpleNamespace(id=3, is_active=True)
    expired = SimpleNamespace(
        id=9, tenant_id=7, plan_id=1, status="cancelled", billing_cycle="monthly",
        starts_at=now - timedelta(days=60), ends_at=now - timedelta(days=30),
        trial_ends_at=None, next_billing_date=None, cancelled_at=now - timedelta(days=30),
        is_auto_renew=True,
    )
    db = _DB(tenant, plan, expired)

    result = lifecycle.renew_subscription(db, 7)

    assert result is expired
    assert result.status == "active"
    assert result.starts_at >= now - timedelta(seconds=2)
    assert result.ends_at > result.starts_at
    assert result.next_billing_date == result.ends_at
    assert tenant.is_active is True
    assert tenant.is_trial is False
    assert tenant.suspended_at is None


def test_cancel_auto_renew_keeps_access_until_existing_end_date():
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=10)
    tenant = SimpleNamespace(id=7)
    plan = SimpleNamespace(id=3, is_active=True)
    subscription = SimpleNamespace(
        id=9, tenant_id=7, plan_id=3, status="active", billing_cycle="monthly",
        starts_at=now - timedelta(days=20), ends_at=end, trial_ends_at=None,
        next_billing_date=end, cancelled_at=None, is_auto_renew=True,
    )
    db = _DB(tenant, plan, subscription)

    result = lifecycle.cancel_auto_renewal(db, 7)

    assert result.is_auto_renew is False
    assert result.next_billing_date is None
    assert result.cancelled_at is not None
    assert result.ends_at == end


def test_suspend_requires_reason():
    db = _DB(SimpleNamespace(id=7), SimpleNamespace(id=3, is_active=True), None)

    with pytest.raises(HTTPException) as exc:
        lifecycle.suspend_tenant(db, 7, "   ")

    assert exc.value.status_code == 422
