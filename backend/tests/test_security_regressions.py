from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.modules.commerce.service import CommerceService
from app.modules.platform.subscriptions.service import SubscriptionService
from app.modules.inventory.stock_moves.service import InventoryStockMoveService


class _DB:
    def __init__(self, scalar_result):
        self.scalar_result = scalar_result

    def scalar(self, _query):
        return self.scalar_result


def test_subscription_service_rejects_future_subscription_access():
    future = datetime.now(timezone.utc) + timedelta(days=1)
    subscription = SimpleNamespace(
        status="active",
        starts_at=future,
        ends_at=future + timedelta(days=30),
        trial_ends_at=None,
    )
    assert SubscriptionService._subscription_is_current(subscription) is False


def test_subscription_service_rejects_expired_subscription_access():
    past = datetime.now(timezone.utc) - timedelta(days=1)
    subscription = SimpleNamespace(
        status="active",
        starts_at=past - timedelta(days=30),
        ends_at=past,
        trial_ends_at=None,
    )
    assert SubscriptionService._subscription_is_current(subscription) is False


def test_subscription_service_accepts_current_trial():
    now = datetime.now(timezone.utc)
    subscription = SimpleNamespace(
        status="trialing",
        starts_at=now - timedelta(days=1),
        ends_at=now + timedelta(days=10),
        trial_ends_at=now + timedelta(days=5),
    )
    assert SubscriptionService._subscription_is_current(subscription) is True


def test_commerce_payment_rejects_draft_invoice(monkeypatch):
    service = CommerceService()
    document = SimpleNamespace(document_type="invoice", status="draft", id=10, total=Decimal("100"), paid_total=Decimal("0"))
    called = False

    def _post(*args, **kwargs):
        nonlocal called
        called = True
        return document, SimpleNamespace()

    monkeypatch.setattr("app.modules.commerce.service.post_payment", _post)
    payload = SimpleNamespace(
        document_id=10,
        company_id=7,
        amount=Decimal("10"),
        wht_amount=Decimal("0"),
        auto_wht=False,
        payment_date=datetime.now(timezone.utc).date(),
        method="cash",
        reference=None,
        notes=None,
        idempotency_key=None,
    )

    with pytest.raises(ValueError, match="confirmed or posted"):
        service.pay(_DB(document), payload, "sale")
    assert called is False


def test_commerce_payment_rejects_credit_note_as_receivable_payment():
    service = CommerceService()
    document = SimpleNamespace(document_type="credit_note", status="confirmed", id=10, total=Decimal("100"), paid_total=Decimal("0"))
    payload = SimpleNamespace(
        document_id=10,
        company_id=7,
        amount=Decimal("10"),
        wht_amount=Decimal("0"),
        auto_wht=False,
        payment_date=datetime.now(timezone.utc).date(),
        method="cash",
        reference=None,
        notes=None,
        idempotency_key=None,
    )
    with pytest.raises(ValueError, match="only for invoices and bills"):
        service.pay(_DB(document), payload, "sale")


def test_stock_issue_rejects_reserved_quantity(monkeypatch):
    service = InventoryStockMoveService()
    move = SimpleNamespace(
        id=1,
        status="draft",
        item_id=5,
        source_location_id=10,
        destination_location_id=None,
        movement_type="issue",
        quantity=Decimal("8"),
        unit_cost=Decimal("0"),
    )
    item = SimpleNamespace(item_type="stockable", costing_method="standard", standard_cost=Decimal("10"), purchase_price=Decimal("10"))
    balance = SimpleNamespace(quantity_on_hand=Decimal("10"), quantity_reserved=Decimal("5"), location=SimpleNamespace(warehouse_id=2))

    monkeypatch.setattr(service, "_location_balance", lambda *args, **kwargs: balance)
    monkeypatch.setattr(service, "_warehouse_stock", lambda *args, **kwargs: SimpleNamespace(quantity_on_hand=Decimal("10"), quantity_reserved=Decimal("5"), average_cost=Decimal("10")))

    class FakeDB:
        def scalar(self, query):
            text = str(query)
            if "inventory_stock_moves" in text:
                return move
            if "product_variants" in text:
                return None
            return item

    with pytest.raises(ValueError, match="reserved for another transaction"):
        service.post(FakeDB(), tenant_id=7, company_id=7, move_id=1, user_id=1)
