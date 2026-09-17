from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.modules.saas.entitlements import _active_subscription


class _Result:
    def __init__(self, values):
        self._values = values

    def all(self):
        return list(self._values)


class _DB:
    def __init__(self, subscription, plan):
        self.subscription = subscription
        self.plan = plan

    def scalars(self, _statement):
        return _Result([self.subscription])

    def get(self, model, _id):
        return self.plan


@pytest.mark.parametrize("status", ["past_due", "grace"])
def test_paid_entitlements_remain_available_before_subscription_end(status):
    now = datetime.now(timezone.utc)
    subscription = SimpleNamespace(
        status=status,
        starts_at=now - timedelta(days=2),
        ends_at=now + timedelta(days=1),
        trial_ends_at=None,
        plan_id=10,
    )
    plan = SimpleNamespace(grace_period_days=7)

    assert _active_subscription(_DB(subscription, plan), 7) is subscription


def test_grace_entitlement_survives_past_nominal_end_within_grace_window():
    now = datetime.now(timezone.utc)
    subscription = SimpleNamespace(
        status="grace",
        starts_at=now - timedelta(days=30),
        ends_at=now - timedelta(days=2),
        trial_ends_at=None,
        plan_id=10,
    )
    plan = SimpleNamespace(grace_period_days=7)

    assert _active_subscription(_DB(subscription, plan), 7) is subscription


def test_grace_entitlement_expires_after_plan_grace_window():
    now = datetime.now(timezone.utc)
    subscription = SimpleNamespace(
        status="grace",
        starts_at=now - timedelta(days=30),
        ends_at=now - timedelta(days=8),
        trial_ends_at=None,
        plan_id=10,
    )
    plan = SimpleNamespace(grace_period_days=7)

    assert _active_subscription(_DB(subscription, plan), 7) is None
