from datetime import date, datetime, timezone
from decimal import Decimal

from app.modules.integrations.salla_service import _code, _date, _decimal, _event_key, _dt
from app.modules.integrations.salla_shipping_service import _advance_status


def test_salla_nested_value_helpers_are_safe_and_normalized():
    assert _code({"slug": "paid", "name": "Paid"}) == "paid"
    assert _code({"name": "Cash on delivery"}) == "Cash on delivery"
    assert _code(None) is None
    assert _decimal({"amount": "125.50", "currency": "SAR"}) == Decimal("125.50")
    assert _decimal({"value": "12.5"}) == Decimal("12.5")
    assert _decimal("not-a-number") is None
    assert _dt("2026-09-13T18:30:00Z") == datetime(2026, 9, 13, 18, 30, tzinfo=timezone.utc)
    assert _date("2026-09-13T18:30:00Z") == date(2026, 9, 13)


def test_salla_event_classification_covers_order_shipment_and_invoice_events():
    assert _event_key("order.created") == "order"
    assert _event_key("order.shipment.created") == "order"
    assert _event_key("shipment.created") == "shipment"
    assert _event_key("order.invoice.created") == "invoice"
    assert _event_key("product.updated") == "product"
    assert _event_key("customer.updated") == "customer"
    assert _event_key("something.unknown") == "unknown"


def test_salla_shipping_terminal_events_do_not_get_lost():
    # Return/cancel terminal events are accepted only when the canonical
    # ERP transition contract permits them.
    assert _advance_status("in_transit", "returned") == "returned"
    assert _advance_status("out_for_delivery", "returned") == "returned"
    assert _advance_status("pending", "returned") == "pending"
    assert _advance_status("in_transit", "cancelled") == "in_transit"
    assert _advance_status("pending", "cancelled") == "cancelled"
    assert _advance_status("delivered", "returned") == "delivered"
    assert _advance_status("delivered", "cancelled") == "delivered"


def test_salla_shipping_normal_progression_remains_ordered():
    assert _advance_status("pending", "picked_up") == "picked_up"
    assert _advance_status("picked_up", "in_transit") == "in_transit"
    assert _advance_status("in_transit", "out_for_delivery") == "out_for_delivery"
    assert _advance_status("out_for_delivery", "delivered") == "delivered"
    assert _advance_status("delivered", "pending") == "delivered"
