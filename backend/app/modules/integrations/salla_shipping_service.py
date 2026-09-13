from __future__ import annotations

from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.integrations.models import IntegrationMapping
from app.modules.integrations.salla_models import SallaOrder, SallaShipment
from app.modules.shipping.models import ShippingCarrier, ShippingMethod, Shipment


_STATUS_MAP = {
    "pending": "pending",
    "created": "pending",
    "ready": "pending",
    "picked_up": "picked_up",
    "pickedup": "picked_up",
    "in_transit": "in_transit",
    "intransit": "in_transit",
    "out_for_delivery": "out_for_delivery",
    "outfordelivery": "out_for_delivery",
    "delivered": "delivered",
    "returned": "returned",
    "return": "returned",
    "cancelled": "cancelled",
    "canceled": "cancelled",
}


def _mapping(db: Session, shipment: SallaShipment) -> IntegrationMapping | None:
    return db.scalar(select(IntegrationMapping).where(IntegrationMapping.company_id == shipment.company_id, IntegrationMapping.connection_id == shipment.connection_id, IntegrationMapping.entity_type == "salla_shipment", IntegrationMapping.external_id == str(shipment.external_id)))


def _order(db: Session, shipment: SallaShipment) -> SallaOrder | None:
    if shipment.order_id:
        return db.scalar(select(SallaOrder).where(SallaOrder.id == shipment.order_id, SallaOrder.company_id == shipment.company_id))
    if shipment.order_external_id:
        return db.scalar(select(SallaOrder).where(SallaOrder.connection_id == shipment.connection_id, SallaOrder.external_id == shipment.order_external_id, SallaOrder.company_id == shipment.company_id))
    return None


def _carrier(db: Session, company_id: int, shipment: SallaShipment) -> ShippingCarrier | None:
    for name in (shipment.courier_name, shipment.external_company_name):
        if name:
            obj = db.scalar(select(ShippingCarrier).where(ShippingCarrier.company_id == company_id, ShippingCarrier.is_active.is_(True), ShippingCarrier.name.ilike(name)).order_by(ShippingCarrier.id))
            if obj:
                return obj
    return None


def _method(db: Session, carrier: ShippingCarrier, shipment: SallaShipment) -> ShippingMethod | None:
    payment = str(shipment.payment_method or "").strip().lower().replace("-", "_").replace(" ", "_")
    preferred = "cod" if payment in {"cod", "cash_on_delivery"} else "prepaid" if payment else "mixed"
    return db.scalar(select(ShippingMethod).where(ShippingMethod.carrier_id == carrier.id, ShippingMethod.payment_method == preferred).order_by(ShippingMethod.id)) or db.scalar(select(ShippingMethod).where(ShippingMethod.carrier_id == carrier.id).order_by(ShippingMethod.id))


def _advance_status(current: str, target: str) -> str:
    if target == current:
        return current
    if target == "pending":
        return current
    # Salla terminal events are authoritative. They may arrive before all
    # intermediate webhooks, so do not lose a returned/cancelled event.
    if target == "returned":
        return "returned" if current not in {"returned", "cancelled"} else current
    if target == "cancelled":
        return "cancelled" if current not in {"returned", "cancelled", "delivered"} else current
    path = {
        "pending": ["picked_up", "in_transit", "out_for_delivery", "delivered"],
        "picked_up": ["in_transit", "out_for_delivery", "delivered"],
        "in_transit": ["out_for_delivery", "delivered"],
        "out_for_delivery": ["delivered"],
    }.get(current, [])
    if target in path:
        return target
    return current


def sync_salla_shipment(db: Session, salla_shipment: SallaShipment) -> dict:
    existing_map = _mapping(db, salla_shipment)
    if existing_map:
        existing = db.scalar(select(Shipment).where(Shipment.id == existing_map.local_id, Shipment.company_id == salla_shipment.company_id))
        if existing:
            target = _STATUS_MAP.get(str(salla_shipment.status or "").lower().replace(" ", "_"))
            if target:
                existing.status = _advance_status(existing.status, target)
            if salla_shipment.tracking_number and existing.tracking_no != salla_shipment.tracking_number:
                existing.tracking_no = salla_shipment.tracking_number[:100]
            existing.cod_amount = Decimal(salla_shipment.cash_on_delivery or 0)
            if salla_shipment.total is not None:
                existing.shipping_fee = Decimal(salla_shipment.total or 0)
            db.flush()
            return {"status": "updated", "shipment_id": existing.id}

    carrier = _carrier(db, salla_shipment.company_id, salla_shipment)
    if carrier is None:
        return {"status": "pending_configuration", "reason": "No active ERP shipping carrier matches the Salla courier"}
    method = _method(db, carrier, salla_shipment)
    if method is None:
        return {"status": "pending_configuration", "reason": "No ERP shipping method is configured for the matched carrier"}

    order = _order(db, salla_shipment)
    sales_document_id = None
    customer_name = "Salla Customer"
    if order:
        mapping = db.scalar(select(IntegrationMapping).where(IntegrationMapping.company_id == order.company_id, IntegrationMapping.connection_id == order.connection_id, IntegrationMapping.entity_type == "salla_order", IntegrationMapping.external_id == str(order.external_id)))
        sales_document_id = mapping.local_id if mapping else None
        customer_name = str(order.customer_id or customer_name)

    tracking = (salla_shipment.tracking_number or salla_shipment.shipping_number or f"SALLA-{salla_shipment.external_id}")[:100]
    cod = Decimal(salla_shipment.cash_on_delivery or 0)
    fee = Decimal(salla_shipment.total or 0)
    target_status = _STATUS_MAP.get(str(salla_shipment.status or "").lower().replace(" ", "_"), "pending")
    obj = Shipment(company_id=salla_shipment.company_id, carrier_id=carrier.id, method_id=method.id, sales_document_id=sales_document_id, tracking_no=tracking, status="pending", cod_amount=cod, shipping_fee=fee, customer_name=customer_name[:200], notes=f"Imported from Salla shipment {salla_shipment.external_id}")
    db.add(obj)
    db.flush()
    obj.status = _advance_status(obj.status, target_status)
    db.add(IntegrationMapping(company_id=salla_shipment.company_id, connection_id=salla_shipment.connection_id, entity_type="salla_shipment", external_id=str(salla_shipment.external_id), local_id=obj.id))
    db.flush()
    return {"status": "created", "shipment_id": obj.id}


def sync_salla_shipments_for_order(db: Session, order: SallaOrder) -> list[dict]:
    rows = db.scalars(select(SallaShipment).where(SallaShipment.company_id == order.company_id, SallaShipment.connection_id == order.connection_id, SallaShipment.order_id == order.id).order_by(SallaShipment.id)).all()
    return [sync_salla_shipment(db, row) for row in rows]
