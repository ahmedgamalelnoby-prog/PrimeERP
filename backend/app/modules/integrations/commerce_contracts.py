"""Canonical commerce contracts shared by all commerce-platform adapters.

Platform adapters (Salla, Shopify, WooCommerce, marketplaces, POS connectors, ...)
translate external payloads into these contracts. Core sales/inventory/accounting
modules must consume the canonical objects rather than platform-specific fields.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Mapping


@dataclass(frozen=True)
class CanonicalOrderLine:
    external_line_id: str
    sku: str | None
    item_external_id: str | None
    variant_external_id: str | None
    quantity: Decimal
    unit_price: Decimal
    discount: Decimal = Decimal("0")
    tax: Decimal = Decimal("0")
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def revenue(self) -> Decimal:
        return self.quantity * self.unit_price - self.discount


@dataclass(frozen=True)
class CanonicalPayment:
    method: str
    amount: Decimal
    paid_amount: Decimal = Decimal("0")
    cod_amount: Decimal = Decimal("0")
    currency: str = "EGP"
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CanonicalShipment:
    external_shipment_id: str
    external_carrier_id: str | None
    carrier_name: str | None
    tracking_number: str | None
    status: str
    raw_status: str | None
    payment_method: str | None
    shipping_fee: Decimal = Decimal("0")
    customer_shipping_fee: Decimal = Decimal("0")
    cod_amount: Decimal = Decimal("0")
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CanonicalOrder:
    platform: str
    connection_id: int
    external_order_id: str
    order_date: Any
    currency: str
    customer_external_id: str | None
    status: str
    lines: tuple[CanonicalOrderLine, ...]
    payments: tuple[CanonicalPayment, ...] = ()
    shipments: tuple[CanonicalShipment, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def merchandise_revenue(self) -> Decimal:
        return sum((line.revenue for line in self.lines), Decimal("0"))

    @property
    def shipping_revenue(self) -> Decimal:
        return sum((s.customer_shipping_fee for s in self.shipments), Decimal("0"))

    @property
    def total_cod(self) -> Decimal:
        return sum((p.cod_amount for p in self.payments), Decimal("0"))


CANONICAL_SHIPMENT_STATUSES = frozenset({
    "pending", "picked_up", "in_transit", "out_for_delivery",
    "delivered", "delivery_failed", "reattempted", "cancelled",
    "return_in_transit", "returned",
})


def normalize_payment_method(value: str | None) -> str:
    raw = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if raw in {"cod", "cash_on_delivery"}:
        return "cod"
    if raw in {"card", "credit_card", "debit_card", "mada", "prepaid", "pre_paid", "paid"}:
        return "prepaid"
    if raw in {"bank", "bank_transfer", "transfer"}:
        return "bank_transfer"
    return raw or "unknown"
