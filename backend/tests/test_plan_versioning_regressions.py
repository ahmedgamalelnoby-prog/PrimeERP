from types import SimpleNamespace

import pytest

from app.modules.platform.plans.exceptions import PlanValidationError
from app.modules.platform.plans.schemas import PlanCreate
from app.modules.platform.plans.service import PlanService


class _Query:
    def __init__(self, row):
        self.row = row

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def with_for_update(self):
        return self

    def first(self):
        return self.row


class _DB:
    def __init__(self, latest):
        self.latest = latest

    def query(self, model):
        return _Query(self.latest)

    def commit(self):
        return None


class _Repository:
    def __init__(self, source):
        self.source = source
        self.created = None

    def get_by_id(self, db, plan_id, for_update=False):
        return self.source

    def get_default(self, db):
        return self.source if self.source.is_default else None

    def create(self, db, data):
        self.created = data
        return SimpleNamespace(**data)

    def refresh(self, db, instance):
        return None


def _schema(**overrides):
    data = {
        "code": "pro",
        "name": "Pro",
        "monthly_price": "100.00",
        "yearly_price": "1000.00",
        "currency": "EGP",
        "billing_cycle": "monthly",
        "trial_days": 14,
        "grace_period_days": 7,
        "max_users": 10,
        "max_companies": 1,
        "max_branches": 5,
        "max_products": 1000,
        "max_integrations": 3,
        "storage_limit_mb": 1024,
        "is_default": True,
        "is_public": True,
        "is_free": False,
        "is_custom": False,
        "status": "active",
        "plan_type": "standard",
        "sort_order": 1,
    }
    data.update(overrides)
    return PlanCreate(**data)


def test_create_plan_version_keeps_original_plan_row_and_increments_version():
    source = SimpleNamespace(id=10, code="pro", version=1, is_default=True)
    latest = SimpleNamespace(version=1)
    db = _DB(latest=latest)
    repository = _Repository(source)
    service = PlanService(db)
    service.repository = repository

    created = service.create_plan_version(10, _schema())

    assert source.is_default is False
    assert created.version == 2
    assert repository.created["code"] == "pro"
    assert repository.created["version"] == 2
    assert repository.created["monthly_price"] == "100.00"


def test_create_plan_version_rejects_changing_commercial_plan_code():
    source = SimpleNamespace(id=10, code="pro", version=1, is_default=False)
    db = _DB(latest=SimpleNamespace(version=1))
    repository = _Repository(source)
    service = PlanService(db)
    service.repository = repository

    with pytest.raises(PlanValidationError):
        service.create_plan_version(10, _schema(code="enterprise"))

    assert repository.created is None
