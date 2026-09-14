from types import SimpleNamespace

import pytest

from app.modules.platform.subscriptions.service import SubscriptionService


class _DB:
    pass


def _service(subscription, tenant):
    svc = SubscriptionService(_DB())
    svc._get = lambda subscription_id, for_update=False: subscription
    svc._locked_tenant = lambda tenant_id: tenant
    svc._sync_tenant_state = lambda instance: None
    return svc


def test_activate_rejects_cancelled_subscription():
    subscription = SimpleNamespace(status="cancelled", tenant_id=7)
    tenant = SimpleNamespace(status="active", is_active=True)
    svc = _service(subscription, tenant)

    with pytest.raises(ValueError, match="Only trialing or past_due"):
        svc.activate(9)


def test_activate_rejects_suspended_tenant_without_reactivation():
    subscription = SimpleNamespace(
        status="trialing",
        tenant_id=7,
        billing_cycle="monthly",
        is_auto_renew=True,
    )
    tenant = SimpleNamespace(status="suspended", is_active=False)
    svc = _service(subscription, tenant)

    with pytest.raises(ValueError, match="explicit reactivation"):
        svc.activate(9)

    assert subscription.status == "trialing"


def test_convert_to_paid_rejects_suspended_tenant_before_mutation():
    subscription = SimpleNamespace(status="trialing", tenant_id=7)
    tenant = SimpleNamespace(status="suspended", is_active=False)
    svc = _service(subscription, tenant)

    with pytest.raises(ValueError, match="explicit reactivation"):
        svc.convert_to_paid(9, SimpleNamespace(starts_at=None, billing_cycle=None, plan_id=None, ends_at=None, auto_renew=None, notes=None))

    assert subscription.status == "trialing"


def test_create_locks_tenant_before_conflict_check(monkeypatch):
    class Query:
        def filter(self, *args):
            return self

        def with_for_update(self):
            return self

        def first(self):
            return SimpleNamespace(id=7)

    class DB:
        def query(self, model):
            return Query()

    class Repo:
        def get_conflicting_for_tenant(self, *args, **kwargs):
            return None

    svc = SubscriptionService(DB())
    svc.repository = Repo()
    calls = []

    def fake_resolve(plan_id):
        return SimpleNamespace(status="active", trial_days=0)

    def fake_lock(tenant_id):
        calls.append("lock")
        return SimpleNamespace(id=tenant_id)

    svc._resolve_plan = fake_resolve
    svc._locked_tenant = fake_lock

    schema = SimpleNamespace(
        plan_id=1,
        tenant_id=7,
        starts_at=None,
        trial_ends_at=None,
        ends_at=None,
        billing_cycle="monthly",
        auto_renew=False,
        model_dump=lambda: {"tenant_id": 7, "plan_id": 1},
    )

    with pytest.raises(AttributeError):
        svc.create(schema)

    assert calls == ["lock"]
