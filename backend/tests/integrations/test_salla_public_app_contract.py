from decimal import Decimal
import inspect


import pytest

from app.modules.integrations.salla_public_app_router import establish_embedded_session
from app.modules.integrations.salla_public_app_service import (
    SallaPublicAppError,
    _merchant_id,
    _encrypt,
    decrypt_token,
)
from app.modules.integrations.salla_shipping_service import _advance_status
from app.modules.integrations.salla_erp_finalize import _should_fulfill_order, _shipment_package_quantities
from app.modules.integrations.salla_models import SallaOrderItem, SallaShipment
from app.modules.shipping.service import (
    ShippingValidationError,
    calculate_shipping_fee,
    validate_shipment_transition,
)


def test_salla_authorization_identity_and_token_encryption_roundtrip():
    payload = {"merchant": {"id": 987654}, "data": {"access_token": "ignored"}}
    assert _merchant_id(payload) == "987654"

    ciphertext = _encrypt("salla-secret-token")
    assert ciphertext
    assert ciphertext != "salla-secret-token"
    assert decrypt_token(ciphertext) == "salla-secret-token"


def test_salla_authorization_requires_merchant_identity():
    with pytest.raises(SallaPublicAppError, match="merchant id"):
        _merchant_id({"data": {"access_token": "token"}})


@pytest.mark.parametrize(
    ("current", "target", "expected"),
    [
        ("pending", "shipped", "shipped"),
        ("shipped", "in_transit", "in_transit"),
        ("in_transit", "out_for_delivery", "out_for_delivery"),
        ("out_for_delivery", "delivered", "delivered"),
        ("delivered", "pending", "delivered"),
        ("delivered", "cancelled", "delivered"),
        ("returned", "delivered", "returned"),
        ("cancelled", "delivered", "cancelled"),
    ],
)
def test_salla_shipping_status_is_monotonic(current, target, expected):
    assert _advance_status(current, target) == expected


def test_shipping_state_machine_accepts_delivery_and_return():
    validate_shipment_transition("out_for_delivery", "delivered")
    validate_shipment_transition("delivered", "returned")


def test_shipping_state_machine_rejects_backward_transition():
    with pytest.raises(ShippingValidationError):
        validate_shipment_transition("delivered", "out_for_delivery")


def test_shipping_cod_fee_calculation():
    assert calculate_shipping_fee(
        Decimal("25"),
        cod_amount=Decimal("1000"),
        cod_fee_percent=Decimal("2.5"),
        payment_method="cod",
    ) == Decimal("50.00")


def test_shipping_prepaid_rejects_cod_amount():
    with pytest.raises(ShippingValidationError):
        calculate_shipping_fee(
            Decimal("25"),
            cod_amount=Decimal("100"),
            cod_fee_percent=Decimal("2"),
            payment_method="prepaid",
        )


def test_shipping_invalid_rate_is_rejected():
    with pytest.raises(ShippingValidationError):
        calculate_shipping_fee(
            Decimal("25"),
            cod_fee_percent=Decimal("101"),
            payment_method="cod",
        )


def test_salla_embedded_session_accepts_token_from_json_body():
    parameter = inspect.signature(establish_embedded_session).parameters["salla_token"]
    assert getattr(parameter.default, "embed", None) is True


def test_salla_order_does_not_fulfill_from_creation_or_pending_status():
    order = type("Order", (), {"status": "created", "fulfillment_status": "pending"})()
    assert _should_fulfill_order(order) is False


@pytest.mark.parametrize(
    "fulfillment_status",
    ["processing", "shipped", "in_transit", "delivering", "out_for_delivery", "delivered", "fulfilled", "partially_fulfilled"],
)
def test_salla_fulfillment_status_allows_inventory_fulfillment(fulfillment_status):
    order = type("Order", (), {"status": "created", "fulfillment_status": fulfillment_status})()
    assert _should_fulfill_order(order) is True


def test_salla_shipment_milestone_can_explicitly_request_fulfillment():
    order = type("Order", (), {"status": "created", "fulfillment_status": "pending"})()
    assert _should_fulfill_order(order, force_fulfillment=True) is True


@pytest.mark.parametrize(
    "fulfillment_status",
    ["pending", "created", "cancelled"],
)
def test_salla_pending_or_non_fulfillment_states_do_not_consume_inventory(fulfillment_status):
    order = type("Order", (), {"status": "created", "fulfillment_status": fulfillment_status})()
    assert _should_fulfill_order(order) is False


def test_salla_shipment_packages_resolve_item_quantities():
    item_a = SallaOrderItem(id=1, external_id="101", sku="SKU-A", quantity=10)
    item_b = SallaOrderItem(id=2, external_id="102", sku="SKU-B", quantity=3)
    shipment = SallaShipment(
        external_id="S-1",
        packages=[
            {"item_id": 101, "sku": "SKU-A", "quantity": 4},
            {"external_id": "102", "sku": "SKU-B", "quantity": 2},
        ],
    )
    assert _shipment_package_quantities(shipment, [item_a, item_b]) == {
        item_a.id: Decimal("4"),
        item_b.id: Decimal("2"),
    }
