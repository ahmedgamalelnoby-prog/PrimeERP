from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.modules.platform.tenants.service import TenantService
from app.modules.saas.models import Subscription


class _Query:
    def __init__(self, value):
        self.value = value

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def with_for_update(self):
        return self

    def first(self):
        return self.value

    def all(self):
        return self.value


class _DB:
    def __init__(self, subscription=None, subscriptions=None):
        self.subscription = subscription
        self.subscriptions = subscriptions or []
        self.flushed = 0

    def query(self, model):
        if model is Subscription:
            return _Query(self.subscription if self.subscription is not None else self.subscriptions)
        raise AssertionError(f"Unexpected model: {model}")

    def add(self, value):
        return None

    def flush(self):
        self.flushed += 1


def _service(tenant):
    service = TenantService()
    service.get_tenant_or_raise = lambda db, tenant_id, for_update=False: tenant
    return service


def _subscription(status="active", days=30):
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        tenant_id=7,
        status=status,
        starts_at=now - timedelta(days=1),
        ends_at=now + timedelta(days=days),
        trial_ends_at=(now + timedelta(days=days)) if status == "trialing" else None,
        cancelled_at=None,
        is_auto_renew=True,
        next_billing_date=now + timedelta(days=days),
    )


def test_activate_requires_current_subscription():
    tenant = SimpleNamespace(
        id=7, status="suspended", is_active=False, is_trial=False,
        suspended_at="x", suspension_reason="billing",
    )
    service = _service(tenant)
    db = _DB(subscription=None)

    with pytest.raises(Exception, match="no_active_subscription"):
        service.activate_tenant(db, 7)

    assert tenant.status == "suspended"
    assert tenant.is_active is False


def test_resume_requires_current_subscription():
    tenant = SimpleNamespace(
        id=7, status="suspended", is_active=False, is_trial=False,
        suspended_at="x", suspension_reason="billing",
    )
    service = _service(tenant)
    db = _DB(subscription=None)

    with pytest.raises(Exception, match="no_active_subscription"):
        service.resume_tenant(db, 7)

    assert tenant.status == "suspended"
    assert tenant.is_active is False


def test_resume_with_current_subscription_explicitly_reactivates():
    tenant = SimpleNamespace(
        id=7, status="suspended", is_active=False, is_trial=False,
        suspended_at="x", suspension_reason="billing",
    )
    service = _service(tenant)
    db = _DB(subscription=_subscription())

    result = service.resume_tenant(db, 7)

    assert result is tenant
    assert tenant.status == "active"
    assert tenant.is_active is True
    assert tenant.suspended_at is None
    assert tenant.suspension_reason is None


def test_expired_subscription_cannot_resume():
    tenant = SimpleNamespace(
        id=7, status="suspended", is_active=False, is_trial=False,
        suspended_at="x", suspension_reason="expired",
    )
    expired = _subscription(days=-1)
    service = _service(tenant)
    db = _DB(subscription=expired)

    with pytest.raises(Exception, match="no_active_subscription"):
        service.resume_tenant(db, 7)

    assert tenant.status == "suspended"
    assert tenant.is_active is False


def test_cancel_tenant_cancels_open_subscriptions():
    tenant = SimpleNamespace(
        id=7, status="active", is_active=True, is_trial=False,
        suspended_at=None, suspension_reason=None,
    )
    active = _subscription()
    trial = _subscription(status="trialing")
    service = _service(tenant)
    db = _DB(subscriptions=[active, trial])

    service.cancel_tenant(db, 7)

    assert tenant.status == "cancelled"
    assert tenant.is_active is False
    assert active.status == "cancelled"
    assert trial.status == "cancelled"
    assert active.is_auto_renew is False
    assert trial.is_auto_renew is False
    assert active.next_billing_date is None
    assert trial.next_billing_date is None
