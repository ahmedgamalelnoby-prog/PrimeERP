from types import SimpleNamespace

import pytest

from app.modules.platform.plans.exceptions import PlanValidationError
from app.modules.platform.plans.service import PlanService


class _Query:
    def __init__(self, result):
        self.result = result

    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        return self.result


class _DB:
    def __init__(self, subscription):
        self.subscription = subscription

    def query(self, *_args, **_kwargs):
        return _Query(self.subscription)


def test_subscribed_plan_rejects_commercial_contract_changes():
    service = PlanService(_DB(SimpleNamespace(id=10)))
    plan = SimpleNamespace(id=10)

    with pytest.raises(PlanValidationError, match="immutable"):
        service._validate_referenced_plan_update(
            plan,
            {"monthly_price": 999, "max_users": 100},
        )


def test_subscribed_plan_allows_catalog_only_changes():
    service = PlanService(_DB(SimpleNamespace(id=10)))
    plan = SimpleNamespace(id=10)

    service._validate_referenced_plan_update(
        plan,
        {"is_public": False, "sort_order": 20, "status": "inactive"},
    )


def test_unsubscribed_plan_remains_editable():
    service = PlanService(_DB(None))
    plan = SimpleNamespace(id=10)

    service._validate_referenced_plan_update(
        plan,
        {"monthly_price": 999, "trial_days": 30, "max_users": 100},
    )
