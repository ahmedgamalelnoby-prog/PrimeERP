from decimal import Decimal

import pytest

from app.modules.shipping.service import (
    ShippingValidationError,
    calculate_shipping_fee,
    validate_shipment_transition,
)


def test_prepaid_shipping_uses_base_fee_only():
    assert calculate_shipping_fee("35", payment_method="prepaid") == Decimal("35.00")


def test_cod_shipping_adds_cod_fee():
    assert calculate_shipping_fee("35", "1000", "2.5", "cod") == Decimal("60.00")


def test_prepaid_rejects_cod_amount():
    with pytest.raises(ShippingValidationError):
        calculate_shipping_fee("35", "100", "2", "prepaid")


def test_shipment_status_transition_is_validated():
    validate_shipment_transition("pending", "picked_up")
    with pytest.raises(ShippingValidationError):
        validate_shipment_transition("delivered", "in_transit")
