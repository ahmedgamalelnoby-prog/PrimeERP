from decimal import Decimal

import pytest

from app.modules.integrations.router import _event_identity
from app.modules.shipping.service import ShippingValidationError, calculate_shipping_fee, validate_shipment_transition


def test_shipping_prepaid_rejects_cod():
    with pytest.raises(ShippingValidationError):
        calculate_shipping_fee(Decimal("50"), Decimal("1000"), Decimal("2"), "prepaid")


def test_shipping_cod_fee_is_calculated_and_rounded():
    assert calculate_shipping_fee(Decimal("50"), Decimal("1000"), Decimal("2"), "cod") == Decimal("70.00")


def test_shipping_mixed_allows_cod_and_base_fee():
    assert calculate_shipping_fee("25", "500", "1.5", "mixed") == Decimal("32.50")


def test_shipping_lifecycle_rejects_invalid_transition():
    with pytest.raises(ShippingValidationError):
        validate_shipment_transition("pending", "delivered")


def test_shipping_lifecycle_accepts_normal_delivery_path():
    validate_shipment_transition("pending", "picked_up")
    validate_shipment_transition("picked_up", "in_transit")
    validate_shipment_transition("in_transit", "out_for_delivery")
    validate_shipment_transition("out_for_delivery", "delivered")


def test_salla_event_identity_uses_header_values():
    event_id, event_type = _event_identity(
        {"id": "payload-id", "event": "payload.event"},
        "order.created",
        "header-id",
        b"{}",
    )
    assert event_id == "header-id"
    assert event_type == "order.created"


def test_salla_event_identity_is_deterministic_without_event_id():
    first = _event_identity({"order": {"id": 10}}, "order.created", None, b'{"order":{"id":10}}')
    second = _event_identity({"order": {"id": 10}}, "order.created", None, b'{"order":{"id":10}}')
    assert first == second
    assert first[0].startswith("sha256:")


def test_salla_event_identity_requires_event_type():
    with pytest.raises(Exception):
        _event_identity({"id": "1"}, None, "1", b"{}")


def test_salla_shipping_status_normalization_covers_common_salla_states():
    from app.modules.integrations.salla_shipping_service import _STATUS_MAP
    assert _STATUS_MAP["shipped"] == "shipped"
    assert _STATUS_MAP["received_at_final_hub"] == "in_transit"
    assert _STATUS_MAP["reattempted"] == "out_for_delivery"
    assert _STATUS_MAP["return_to_origin"] == "returned"
    assert _STATUS_MAP["cancelled"] == "cancelled"


def test_salla_shipping_status_does_not_move_backwards():
    from app.modules.integrations.salla_shipping_service import _advance_status
    assert _advance_status("delivered", "in_transit") == "delivered"
    assert _advance_status("shipped", "delivered") == "delivered"
    assert _advance_status("out_for_delivery", "pending") == "out_for_delivery"
    assert _advance_status("in_transit", "returned") == "returned"
    assert _advance_status("shipped", "returned") == "returned"
    assert _advance_status("delivered", "cancelled") == "delivered"


def test_salla_shipping_payment_method_mapping_is_not_cross_bound():
    from app.modules.integrations.salla_shipping_service import _method
    class FakeDB:
        def scalar(self, stmt):
            return None
    class Carrier:
        id = 10
    class Shipment:
        payment_method = "cod"
    assert _method(FakeDB(), Carrier(), Shipment()) is None
