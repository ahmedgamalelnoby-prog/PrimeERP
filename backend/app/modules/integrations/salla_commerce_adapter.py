from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.integrations.commerce_adapter import CommerceAdapter
from app.modules.integrations.commerce_contracts import (
    CanonicalOrder,
    CanonicalOrderLine,
    CanonicalPayment,
    CanonicalShipment,
    normalize_payment_method,
)
from app.modules.integrations.salla_models import SallaOrderItem, SallaShipment


_STATUS = {
    "pending": "pending", "created": "pending", "ready": "pending",
    "processing": "pending", "picked_up": "picked_up", "pickedup": "picked_up",
    "shipped": "picked_up", "in_transit": "in_transit",
    "received_at_final_hub": "in_transit", "out_for_delivery": "out_for_delivery",
    "reattempted": "reattempted", "to_be_reattempted": "delivery_failed",
    "partially_delivered": "out_for_delivery", "delivered": "delivered",
    "cancelled": "cancelled", "canceled": "cancelled",
    "return_to_origin": "returned", "return_in_progress": "return_in_transit",
    "returned": "returned",
}


def _status(value: str | None) -> str:
    return _STATUS.get(str(value or "").strip().lower().replace(" ", "_"), "pending")


class SallaCommerceAdapter(CommerceAdapter):
    provider = "salla"

    def normalize_order(self, db: Session, connection: Any, payload: dict[str, Any]) -> CanonicalOrder:
        external_id = str(payload.get("id") or "")
        items = db.scalars(select(SallaOrderItem).where(
            SallaOrderItem.connection_id == connection.id,
            SallaOrderItem.company_id == connection.company_id,
            SallaOrderItem.order_id == payload.get("id"),
        ).order_by(SallaOrderItem.id)).all()

        lines = tuple(
            CanonicalOrderLine(
                external_line_id=str(item.external_id),
                sku=item.sku,
                item_external_id=str(item.product_external_id) if item.product_external_id else None,
                variant_external_id=str(item.variant_external_id) if item.variant_external_id else None,
                quantity=Decimal(item.quantity or 0),
                unit_price=Decimal(item.price or 0),
                discount=Decimal(item.discount or 0),
                tax=Decimal(item.tax or 0),
                metadata={"name": item.name},
            )
            for item in items
        )

        payments = []
        raw_methods = payload.get("payment_methods") or []
        if not isinstance(raw_methods, list):
            raw_methods = [raw_methods]
        total = Decimal(payload.get("total") or 0)
        cod = Decimal(payload.get("cod_amount") or 0)
        if raw_methods:
            for method in raw_methods:
                if isinstance(method, dict):
                    name = method.get("name") or method.get("type") or method.get("method")
                else:
                    name = str(method)
                normalized = normalize_payment_method(name)
                amount = cod if normalized == "cod" else total
                payments.append(CanonicalPayment(method=normalized, amount=amount, cod_amount=cod if normalized == "cod" else Decimal("0")))
        elif total:
            normalized = normalize_payment_method(payload.get("payment_method"))
            payments.append(CanonicalPayment(method=normalized, amount=total, cod_amount=cod))

        shipments = db.scalars(select(SallaShipment).where(
            SallaShipment.connection_id == connection.id,
            SallaShipment.company_id == connection.company_id,
            SallaShipment.order_id == payload.get("id"),
        ).order_by(SallaShipment.id)).all()
        canonical_shipments = tuple(
            CanonicalShipment(
                external_shipment_id=str(s.external_id),
                external_carrier_id=str(s.courier_id) if s.courier_id else None,
                carrier_name=s.courier_name or s.external_company_name,
                tracking_number=s.tracking_number or s.shipping_number,
                status=_status(s.status),
                raw_status=s.status,
                payment_method=normalize_payment_method(s.payment_method),
                shipping_fee=Decimal(s.total or 0),
                customer_shipping_fee=Decimal(payload.get("shipping") or 0),
                cod_amount=Decimal(s.cash_on_delivery or 0),
            )
            for s in shipments
        )

        return CanonicalOrder(
            platform=self.provider,
            connection_id=connection.id,
            external_order_id=external_id,
            order_date=payload.get("created_at") or payload.get("created_at_salla"),
            currency=str(payload.get("currency") or "EGP"),
            customer_external_id=str(payload.get("customer_id")) if payload.get("customer_id") else None,
            status=str(payload.get("status") or "pending"),
            lines=lines,
            payments=tuple(payments),
            shipments=canonical_shipments,
            metadata={"store_id": payload.get("store_id")},
        )
