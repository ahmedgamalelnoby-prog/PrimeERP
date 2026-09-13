from types import SimpleNamespace
from unittest.mock import MagicMock

from app.modules.platform.subscriptions.service import SubscriptionService


def test_subscription_period_days_cover_all_billing_cycles():
    assert SubscriptionService._period_days("monthly") == 30
    assert SubscriptionService._period_days("quarterly") == 90
    assert SubscriptionService._period_days("semi_annual") == 182
    assert SubscriptionService._period_days("yearly") == 365


def _service_with_tenant(tenant):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = tenant
    service = SubscriptionService.__new__(SubscriptionService)
    service.db = db
    service.repository = MagicMock()
    service._sync_tenant_state = MagicMock()
    return service, db


def test_reconcile_repairs_stale_tenant_state_for_active_subscription():
    tenant = SimpleNamespace(
        is_active=False,
        is_trial=True,
        status="suspended",
        trial_ends_at="stale",
    )
    service, db = _service_with_tenant(tenant)
    subscription = SimpleNamespace(status="active", trial_ends_at=None)

    service._reconcile_tenant_state_if_needed(subscription)

    service._sync_tenant_state.assert_called_once_with(subscription)
    db.commit.assert_called_once()


def test_reconcile_does_not_write_when_tenant_state_matches_subscription():
    tenant = SimpleNamespace(
        is_active=True,
        is_trial=False,
        status="active",
        trial_ends_at=None,
    )
    service, db = _service_with_tenant(tenant)
    subscription = SimpleNamespace(status="active", trial_ends_at=None)

    service._reconcile_tenant_state_if_needed(subscription)

    service._sync_tenant_state.assert_not_called()
    db.commit.assert_not_called()
