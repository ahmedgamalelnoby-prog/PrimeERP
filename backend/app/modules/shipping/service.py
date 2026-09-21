from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


class ShippingValidationError(ValueError):
    """Raised when shipping configuration or charges are invalid."""


SUPPORTED_PAYMENT_METHODS = {"prepaid", "cod", "mixed"}


def calculate_shipping_fee(
    base_fee: Decimal | int | float | str,
    cod_amount: Decimal | int | float | str = 0,
    cod_fee_percent: Decimal | int | float | str = 0,
    payment_method: str = "prepaid",
) -> Decimal:
    """Return the final shipping charge, including COD fees when applicable."""
    method = str(payment_method).strip().lower()
    if method not in SUPPORTED_PAYMENT_METHODS:
        raise ShippingValidationError("Invalid shipping payment method")
    base = Decimal(str(base_fee))
    cod = Decimal(str(cod_amount))
    rate = Decimal(str(cod_fee_percent))
    if base < 0 or cod < 0:
        raise ShippingValidationError("Shipping amounts cannot be negative")
    if rate < 0 or rate > 100:
        raise ShippingValidationError("COD fee rate must be between 0 and 100")
    if method == "prepaid" and cod > 0:
        raise ShippingValidationError("COD amount is not allowed for prepaid shipping")
    fee = base
    if method in {"cod", "mixed"} and cod > 0:
        fee += cod * rate / Decimal("100")
    return fee.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# Delivered is a terminal business state. A return after delivery must be
# represented by a separate return workflow, not by reopening the shipment.
SHIPMENT_TRANSITIONS = {
    "pending": {"picked_up", "cancelled"},
    "picked_up": {"in_transit", "cancelled"},
    "in_transit": {"out_for_delivery", "returned"},
    "out_for_delivery": {"delivered", "returned"},
    "delivered": set(),
    "returned": set(),
    "cancelled": set(),
}


def validate_shipment_transition(current: str, target: str) -> None:
    if target not in SHIPMENT_TRANSITIONS:
        raise ShippingValidationError(f"Unknown shipment status: {target}")
    if target == current:
        return
    if target not in SHIPMENT_TRANSITIONS.get(current, set()):
        raise ShippingValidationError(f"Invalid shipment transition: {current} -> {target}")
