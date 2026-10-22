from decimal import Decimal
from datetime import datetime, timedelta, timezone
import importlib
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

transaction_service_module = importlib.import_module("app.modules.transactions.services.transaction_service")
from app.modules.accounting.tax_engine import money


def test_company_rounding_policy_modes():
    amount = Decimal("1.005")
    assert money(amount, "half_up") == Decimal("1.01")
    assert money(amount, "bankers") == Decimal("1.00")
    assert money(amount, "none") == Decimal("1.005")


def test_requester_cannot_approve_own_transaction_when_company_policy_disables_it(monkeypatch):
    service = transaction_service_module.transaction_service
    transaction = SimpleNamespace(id=100, company_id=7, tenant_id=3, created_by=42, status="pending")
    monkeypatch.setattr(service, "_get_locked", lambda **_kwargs: transaction)
    monkeypatch.setattr(
        transaction_service_module,
        "get_company_setting",
        lambda _db, _company_id, key: False if key == "workflow.allow_self_approval" else None,
    )

    with pytest.raises(HTTPException) as exc:
        service.approve_transaction(
            db=object(),
            transaction_id=100,
            current_user=SimpleNamespace(id=42),
        )

    assert exc.value.status_code == 409
    assert "does not allow" in exc.value.detail.lower()



def test_required_branch_policy_blocks_generic_transaction_without_branch(monkeypatch):
    service = transaction_service_module.transaction_service
    monkeypatch.setattr(service, "_get_tenant_id", lambda _user: 3)
    monkeypatch.setattr(service, "_validate_scope", lambda **_kwargs: None)
    monkeypatch.setattr(
        transaction_service_module,
        "get_company_setting",
        lambda _db, _company_id, key: key == "general.branch_required",
    )

    payload = SimpleNamespace(company_id=7, branch_id=None, project_id=None, source_id=None)
    with pytest.raises(HTTPException) as exc:
        service.create_transaction(
            db=object(),
            payload=payload,
            current_user=SimpleNamespace(id=42),
        )

    assert exc.value.status_code == 422
    assert "requires a branch" in exc.value.detail.lower()



def test_disabled_customer_credit_limit_policy_skips_limit_check(monkeypatch):
    from app.modules.commerce import service as commerce_service_module

    service = commerce_service_module.commerce_service
    monkeypatch.setattr(
        commerce_service_module,
        "get_company_setting",
        lambda _db, _company_id, key: False if key == "sales.credit_limit_enforced" else None,
    )
    # If the policy is disabled, no customer lookup or exposure calculation is needed.
    service.enforce_credit_limit(
        db=object(),
        company_id=7,
        document=SimpleNamespace(document_type="invoice", partner_id=10, total=Decimal("500")),
    )



def test_duplicate_customer_policy_blocks_matching_customer(monkeypatch):
    from app.modules.commerce import service as commerce_service_module

    class FakeDB:
        def __init__(self):
            self.calls = 0

        def scalar(self, _query):
            self.calls += 1
            return None if self.calls == 1 else 123

    monkeypatch.setattr(
        commerce_service_module,
        "get_company_setting",
        lambda _db, _company_id, key: key == "crm.duplicate_customer_check",
    )
    payload = SimpleNamespace(
        company_id=7,
        code="C-100",
        partner_type="customer",
        email="same@example.com",
        tax_number=None,
        model_dump=lambda: {},
    )

    with pytest.raises(ValueError, match="Possible duplicate customer"):
        commerce_service_module.commerce_service.create_partner(FakeDB(), payload)



def test_pos_discount_above_no_approval_limit_is_blocked(monkeypatch):
    from app.modules.pos import router as pos_router_module

    monkeypatch.setattr(
        pos_router_module,
        "get_company_setting",
        lambda _db, _company_id, key: {
            "pos.allow_discount_without_approval": True,
            "pos.max_discount_pct_without_approval": 5,
        }[key],
    )
    with pytest.raises(HTTPException) as exc:
        pos_router_module._validate_discount_policy(object(), 7, Decimal("10"))
    assert exc.value.status_code == 409
    assert "maximum" in exc.value.detail.lower()


def test_pos_discount_is_blocked_when_approval_is_required(monkeypatch):
    from app.modules.pos import router as pos_router_module

    monkeypatch.setattr(
        pos_router_module,
        "get_company_setting",
        lambda _db, _company_id, key: {
            "pos.allow_discount_without_approval": False,
            "pos.max_discount_pct_without_approval": 5,
        }[key],
    )
    with pytest.raises(HTTPException) as exc:
        pos_router_module._validate_discount_policy(object(), 7, Decimal("1"))
    assert exc.value.status_code == 409
    assert "requires approval" in exc.value.detail.lower()


def test_pos_discount_within_company_limit_is_allowed(monkeypatch):
    from app.modules.pos import router as pos_router_module

    monkeypatch.setattr(
        pos_router_module,
        "get_company_setting",
        lambda _db, _company_id, key: {
            "pos.allow_discount_without_approval": True,
            "pos.max_discount_pct_without_approval": 5,
        }[key],
    )
    pos_router_module._validate_discount_policy(object(), 7, Decimal("5"))


def test_period_lookup_can_select_date_covering_closed_period_when_lock_disabled():
    from app.modules.accounting.fiscal_years.models import AccountingPeriod
    from app.modules.accounting.fiscal_years.repositories.fiscal_year_repository import FiscalYearRepository
    from datetime import date

    class Query:
        def __init__(self):
            self.filters = []
            self.ordering = []

        def filter(self, *conditions):
            self.filters.extend(conditions)
            return self

        def order_by(self, *expressions):
            self.ordering.extend(expressions)
            return self

        def first(self):
            return "date-covering-period"

    class DB:
        def __init__(self):
            self.query_object = Query()

        def query(self, _model):
            assert _model is AccountingPeriod
            return self.query_object

    db = DB()
    result = FiscalYearRepository().get_period_for_date(
        db, tenant_id=3, company_id=7, posting_date=date(2026, 10, 20), require_open=False
    )

    assert result == "date-covering-period"
    rendered_filters = [str(condition) for condition in db.query_object.filters]
    assert any("accounting_periods.start_date" in condition for condition in rendered_filters)
    assert any("accounting_periods.end_date" in condition for condition in rendered_filters)
    assert not any("accounting_periods.status" in condition for condition in rendered_filters)
    assert not any("accounting_periods.allow_posting" in condition for condition in rendered_filters)


def test_period_lookup_requires_open_and_postable_period_by_default():
    from app.modules.accounting.fiscal_years.models import AccountingPeriod
    from app.modules.accounting.fiscal_years.repositories.fiscal_year_repository import FiscalYearRepository
    from datetime import date

    class Query:
        def __init__(self):
            self.filters = []

        def filter(self, *conditions):
            self.filters.extend(conditions)
            return self

        def order_by(self, *_expressions):
            return self

        def first(self):
            return None

    class DB:
        def __init__(self):
            self.query_object = Query()

        def query(self, _model):
            assert _model is AccountingPeriod
            return self.query_object

    db = DB()
    FiscalYearRepository().get_period_for_date(
        db, tenant_id=3, company_id=7, posting_date=date(2026, 10, 20)
    )

    rendered_filters = [str(condition) for condition in db.query_object.filters]
    assert any("accounting_periods.status" in condition for condition in rendered_filters)
    assert any("accounting_periods.allow_posting" in condition for condition in rendered_filters)



def test_company_setting_registry_rejects_invalid_values():
    from app.modules.company_settings.registry import validate_value

    with pytest.raises(ValueError, match="3-letter uppercase currency code"):
        validate_value("general.base_currency", "egp")
    with pytest.raises(ValueError, match="valid IANA timezone"):
        validate_value("general.timezone", "Not/A_Timezone")
    with pytest.raises(ValueError, match="between 0 and 100"):
        validate_value("pos.max_discount_pct_without_approval", 100.1)
    with pytest.raises(ValueError, match="must be true or false"):
        validate_value("inventory.allow_negative_stock", 1)
    with pytest.raises(ValueError, match="Unknown company setting"):
        validate_value("general.not_a_real_setting", True)


def test_company_setting_registry_defaults_match_declared_types():
    from app.modules.company_settings.registry import CATALOG, validate_value

    assert len({item["key"] for item in CATALOG}) == len(CATALOG)
    for item in CATALOG:
        assert validate_value(item["key"], item["default"]) == item["default"]



def test_integration_retry_policy_moves_exhausted_event_to_dead_letter(monkeypatch):
    integrations_router = importlib.import_module("app.modules.integrations.router")

    event = SimpleNamespace(id=9, status="failed", attempts=5, company_id=7)
    class FakeDB:
        committed = False
        def scalar(self, _query):
            return event
        def commit(self):
            self.committed = True

    db = FakeDB()
    monkeypatch.setattr(integrations_router, "_company_for_user", lambda *_args: None)
    monkeypatch.setattr(
        integrations_router,
        "get_company_setting",
        lambda _db, _company_id, key: 5 if key == "integrations.retry_limit" else None,
    )

    with pytest.raises(HTTPException) as exc:
        integrations_router.retry_event(
            event_id=9,
            company_id=7,
            current_user=SimpleNamespace(tenant_id=3),
            db=db,
        )

    assert exc.value.status_code == 409
    assert event.status == "dead_letter"
    assert db.committed is True


def test_integration_retry_policy_allows_retry_below_company_limit(monkeypatch):
    integrations_router = importlib.import_module("app.modules.integrations.router")

    event = SimpleNamespace(
        id=9, status="failed", attempts=2, company_id=7,
        next_attempt_at=None, last_error="previous failure",
    )
    class FakeDB:
        committed = False
        def scalar(self, _query):
            return event
        def commit(self):
            self.committed = True

    db = FakeDB()
    monkeypatch.setattr(integrations_router, "_company_for_user", lambda *_args: None)
    monkeypatch.setattr(
        integrations_router,
        "get_company_setting",
        lambda _db, _company_id, key: 5 if key == "integrations.retry_limit" else None,
    )
    def process_event(_db, _event):
        _event.status = "processed"
        return {"ok": True}
    monkeypatch.setattr(integrations_router, "_process_event", process_event)

    result = integrations_router.retry_event(
        event_id=9,
        company_id=7,
        current_user=SimpleNamespace(tenant_id=3),
        db=db,
    )

    assert result["status"] == "processed"
    assert event.attempts == 3
    assert event.status == "processed"
    assert event.last_error is None
    assert db.committed is True



def test_salla_webhook_signature_accepts_valid_hmac(monkeypatch):
    import hashlib
    import hmac
    from app.modules.integrations.router import _verify_salla_signature

    secret = "local-test-secret"
    body = b'{"event":"order.created","id":"evt-1"}'
    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    monkeypatch.setenv("PRIMEERP_TEST_SALLA_SECRET", secret)

    _verify_salla_signature(
        SimpleNamespace(webhook_secret_env="PRIMEERP_TEST_SALLA_SECRET"),
        body,
        "Signature",
        signature,
    )


def test_salla_webhook_signature_rejects_invalid_hmac(monkeypatch):
    from app.modules.integrations.router import _verify_salla_signature

    monkeypatch.setenv("PRIMEERP_TEST_SALLA_SECRET", "local-test-secret")
    with pytest.raises(HTTPException) as exc:
        _verify_salla_signature(
            SimpleNamespace(webhook_secret_env="PRIMEERP_TEST_SALLA_SECRET"),
            b'{"event":"order.created"}',
            "Signature",
            "not-a-valid-signature",
        )

    assert exc.value.status_code == 401


def test_salla_webhook_signature_rejects_missing_signature():
    from app.modules.integrations.router import _verify_salla_signature

    with pytest.raises(HTTPException) as exc:
        _verify_salla_signature(
            SimpleNamespace(webhook_secret_env="PRIMEERP_TEST_SALLA_SECRET"),
            b"{}",
            "Signature",
            None,
        )

    assert exc.value.status_code == 401



def test_company_webhook_signature_policy_is_enforced_by_public_endpoint(monkeypatch):
    import asyncio
    integrations_router = importlib.import_module("app.modules.integrations.router")

    connection = SimpleNamespace(
        id=12,
        company_id=7,
        webhook_secret_env="PRIMEERP_TEST_SALLA_SECRET",
    )

    class FakeRequest:
        headers = {}

        async def body(self):
            return b'{"event":"order.created","id":"evt-endpoint"}'

    monkeypatch.setattr(
        integrations_router,
        "_get_salla_connection",
        lambda _db, _connection_id: connection,
    )
    monkeypatch.setattr(
        integrations_router,
        "get_company_setting",
        lambda _db, _company_id, key: key == "integrations.webhook_signature_required",
    )

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            integrations_router.receive_salla_webhook_public(
                connection_id=12,
                request=FakeRequest(),
                x_salla_security_strategy="Signature",
                x_salla_signature=None,
                x_salla_event=None,
                x_salla_event_id=None,
                db=object(),
            )
        )

    assert exc.value.status_code == 401
    assert "signature" in exc.value.detail.lower()



def test_scheduled_integration_sync_respects_company_policy(monkeypatch):
    from app.modules.company_settings.consumers import integrations as policy_module

    monkeypatch.setattr(policy_module, "automatic_sync_enabled", lambda _db, company_id: company_id == 8)
    now = datetime(2026, 10, 22, 9, 0, tzinfo=timezone.utc)

    assert policy_module.integration_sync_due(
        object(), 7, None, interval_minutes=15, now=now
    ) is False
    assert policy_module.integration_sync_due(
        object(), 8, None, interval_minutes=15, now=now
    ) is True


def test_scheduled_integration_sync_observes_interval_and_timezone(monkeypatch):
    from app.modules.company_settings.consumers import integrations as policy_module

    monkeypatch.setattr(policy_module, "automatic_sync_enabled", lambda _db, _company_id: True)
    now = datetime(2026, 10, 22, 9, 15, tzinfo=timezone.utc)
    last_sync = datetime(2026, 10, 22, 9, 0, tzinfo=timezone.utc)

    assert policy_module.integration_sync_due(
        object(), 7, last_sync, interval_minutes=15, now=now
    ) is True
    assert policy_module.integration_sync_due(
        object(), 7, last_sync + timedelta(minutes=1), interval_minutes=15, now=now
    ) is False

@pytest.mark.parametrize(
    ("allow_overproduction", "expected_error"),
    [
        (False, "cannot exceed the planned quantity"),
        (True, "positive inventory valuation"),
    ],
)
def test_manufacturing_overproduction_policy_controls_work_order_completion(
    monkeypatch, allow_overproduction, expected_error
):
    from app.modules.manufacturing.production_orders import service as manufacturing_service_module

    service = manufacturing_service_module.manufacturing_work_order_service
    order = SimpleNamespace(
        id=9,
        status="released",
        planned_quantity=Decimal("5"),
        lines=[],
    )
    monkeypatch.setattr(service, "get", lambda *_args, **_kwargs: order)
    monkeypatch.setattr(
        manufacturing_service_module,
        "get_company_setting",
        lambda _db, _company_id, key: (
            allow_overproduction if key == "manufacturing.allow_overproduction" else None
        ),
    )

    with pytest.raises(ValueError, match=expected_error):
        service.complete(
            db=object(),
            tenant_id=3,
            company_id=7,
            work_order_id=9,
            produced_quantity=Decimal("6"),
            user_id=42,
        )



@pytest.mark.parametrize(
    ("movement_type", "source_module", "source_entity", "source_id"),
    [
        ("production_issue", None, None, None),
        ("production_receipt", "manual", "work_order_output", "9"),
    ],
)
def test_required_work_order_policy_blocks_unlinked_production_stock_moves(
    monkeypatch, movement_type, source_module, source_entity, source_id
):
    from app.modules.inventory.stock_moves import service as stock_move_module

    monkeypatch.setattr(
        stock_move_module,
        "get_company_setting",
        lambda _db, _company_id, key: True if key == "manufacturing.require_work_order" else None,
    )
    payload = SimpleNamespace(
        company_id=7,
        movement_type=movement_type,
        source_module=source_module,
        source_entity=source_entity,
        source_id=source_id,
    )

    with pytest.raises(ValueError, match="work-order completion workflow"):
        stock_move_module.InventoryStockMoveService._validate_required_work_order(object(), payload)


def test_required_work_order_policy_rejects_nonexistent_work_order_material_line(monkeypatch):
    from app.modules.inventory.stock_moves import service as stock_move_module

    class FakeDB:
        def execute(self, _statement):
            return SimpleNamespace(first=lambda: None)

    monkeypatch.setattr(
        stock_move_module,
        "get_company_setting",
        lambda _db, _company_id, key: key == "manufacturing.require_work_order",
    )
    payload = SimpleNamespace(
        company_id=7,
        movement_type="production_issue",
        source_module="manufacturing",
        source_entity="work_order_material",
        source_id="999999",
    )

    with pytest.raises(ValueError, match="released company work order"):
        stock_move_module.InventoryStockMoveService._validate_required_work_order(
            FakeDB(), payload, from_work_order=True
        )
