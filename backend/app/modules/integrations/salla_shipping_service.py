from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.integrations.models import IntegrationMapping
from app.modules.integrations.salla_models import SallaCustomer, SallaOrder, SallaShipment
from app.modules.shipping.models import ShippingCarrier, ShippingMethod, Shipment
from app.modules.shipping.integration import find_mapped_carrier, link_carrier
from app.modules.shipping.status_service import shipping_status_service
from app.modules.integrations.salla_erp_service import _system_user_id


_STATUS_MAP = {
    "pending": "pending",
    "created": "pending",
    "ready": "pending",
    "picked_up": "shipped",
    "pickedup": "picked_up",
    "shipped": "shipped",
    "in_transit": "in_transit",
    "intransit": "in_transit",
    "received_at_final_hub": "in_transit",
    "out_for_delivery": "out_for_delivery",
    "outfordelivery": "out_for_delivery",
    "reattempted": "out_for_delivery",
    "to_be_reattempted": "out_for_delivery",
    "partially_delivered": "out_for_delivery",
    "delivered": "delivered",
    "returned": "returned",
    "return": "returned",
    "return_to_origin": "returned",
    "return_in_progress": "returned",
    "cancelled": "cancelled",
    "canceled": "cancelled",
}


def _mapping(db: Session, shipment: SallaShipment) -> IntegrationMapping | None:
    return db.scalar(
        select(IntegrationMapping).where(
            IntegrationMapping.company_id == shipment.company_id,
            IntegrationMapping.connection_id == shipment.connection_id,
            IntegrationMapping.entity_type == "salla_shipment",
            IntegrationMapping.external_id == str(shipment.external_id),
        )
    )


def _order(db: Session, shipment: SallaShipment) -> SallaOrder | None:
    if shipment.order_id:
        return db.scalar(
            select(SallaOrder).where(
                SallaOrder.id == shipment.order_id,
                SallaOrder.company_id == shipment.company_id,
                SallaOrder.connection_id == shipment.connection_id,
            )
        )
    if shipment.order_external_id:
        return db.scalar(
            select(SallaOrder).where(
                SallaOrder.connection_id == shipment.connection_id,
                SallaOrder.external_id == shipment.order_external_id,
                SallaOrder.company_id == shipment.company_id,
            )
        )
    return None


def _carrier(db: Session, company_id: int, shipment: SallaShipment) -> ShippingCarrier | None:
    # Prefer the immutable Salla courier/company id. Names are only a safe
    # bootstrap fallback when the store was linked before the mapping existed.
    courier_id = str(shipment.courier_id or "").strip()
    if courier_id:
        carrier = find_mapped_carrier(
            db,
            company_id=company_id,
            connection_id=shipment.connection_id,
            external_carrier_id=courier_id,
        )
        if carrier:
            return carrier

    for name in (shipment.courier_name, shipment.external_company_name):
        candidate = str(name or "").strip()
        if not candidate:
            continue
        obj = db.scalar(select(ShippingCarrier).where(
            ShippingCarrier.company_id == company_id,
            ShippingCarrier.is_active.is_(True),
            func.lower(func.trim(ShippingCarrier.name)) == candidate.lower(),
        ).order_by(ShippingCarrier.id))
        if obj:
            if courier_id:
                existing = db.scalar(select(IntegrationMapping).where(
                    IntegrationMapping.company_id == company_id,
                    IntegrationMapping.connection_id == shipment.connection_id,
                    IntegrationMapping.entity_type == "shipping_carrier",
                    IntegrationMapping.external_id == courier_id,
                ))
                if existing:
                    existing.local_id = obj.id
                else:
                    db.add(IntegrationMapping(
                        company_id=company_id,
                        connection_id=shipment.connection_id,
                        entity_type="shipping_carrier",
                        external_id=courier_id,
                        local_id=obj.id,
                    ))
                db.flush()
            return obj
    return None


def _method(db: Session, carrier: ShippingCarrier, shipment: SallaShipment) -> ShippingMethod | None:
    payment = str(shipment.payment_method or "").strip().lower().replace("-", "_").replace(" ", "_")
    if payment in {"cod", "cash_on_delivery"}:
        preferred = ("cod", "mixed")
    elif payment in {"pre_paid", "prepaid", "paid", "card", "mada"}:
        preferred = ("prepaid", "mixed")
    else:
        preferred = ("mixed", "prepaid", "cod")
    for kind in preferred:
        method = db.scalar(select(ShippingMethod).where(
            ShippingMethod.carrier_id == carrier.id,
            ShippingMethod.payment_method == kind,
        ).order_by(ShippingMethod.id))
        if method:
            return method
    # Never silently bind a COD shipment to a prepaid-only method (or vice
    # versa). Missing configuration is explicit and retryable.
    return None


def _advance_status(current: str, target: str) -> str:
    if target == current:
        return current
    if target == "pending":
        return current
    # Salla terminal events are authoritative and may arrive without intermediate events.
    if target == "returned":
        return "returned" if current not in {"returned", "cancelled"} else current
    if target == "cancelled":
        # Delivered/returned are terminal and must not be downgraded by a
        # late cancellation webhook.
        return "cancelled" if current not in {"delivered", "returned", "cancelled"} else current
    path = {
        "pending": ["picked_up", "in_transit", "out_for_delivery", "delivered"],
        "picked_up": ["in_transit", "out_for_delivery", "delivered"],
        "in_transit": ["out_for_delivery", "delivered"],
        "out_for_delivery": ["delivered"],
    }.get(current, [])
    if target in path:
        return target
    return current


def _customer_name(db: Session, order: SallaOrder | None, fallback: str = "Salla Customer") -> str:
    if not order or not order.customer_id:
        return fallback
    customer = db.scalar(
        select(SallaCustomer).where(
            SallaCustomer.company_id == order.company_id,
            SallaCustomer.connection_id == order.connection_id,
            SallaCustomer.external_id == order.customer_id,
        )
    )
    if not customer:
        return fallback
    name = " ".join(
        part.strip() for part in (customer.first_name, customer.last_name) if isinstance(part, str) and part.strip()
    )
    return name[:200] if name else fallback


def sync_salla_shipment(db: Session, salla_shipment: SallaShipment) -> dict:
    existing_map = _mapping(db, salla_shipment)
    if existing_map:
        existing = db.scalar(
            select(Shipment).where(
                Shipment.id == existing_map.local_id,
                Shipment.company_id == salla_shipment.company_id,
            )
        )
        if existing:
            target = _STATUS_MAP.get(str(salla_shipment.status or "").lower().replace(" ", "_"))
            if target:
                target = _advance_status(existing.status, target)
                if target != existing.status:
                    shipping_status_service.apply_transition(
                        db, existing, target,
                        changed_on=salla_shipment.created_at_salla.date() if salla_shipment.created_at_salla else None,
                        user_id=_system_user_id(db, salla_shipment.company_id),
                    )
            if salla_shipment.tracking_number and existing.tracking_no != salla_shipment.tracking_number:
                existing.tracking_no = salla_shipment.tracking_number[:100]
            existing.cod_amount = Decimal(salla_shipment.cash_on_delivery or 0)
            if salla_shipment.total is not None:
                existing.shipping_fee = Decimal(salla_shipment.total or 0)
            db.flush()
            return {"status": "updated", "shipment_id": existing.id}

    carrier = _carrier(db, salla_shipment.company_id, salla_shipment)
    if carrier is None:
        return {
            "status": "pending_configuration",
            "reason": "No active ERP shipping carrier matches the Salla courier",
        }
    method = _method(db, carrier, salla_shipment)
    if method is None:
        return {
            "status": "pending_configuration",
            "reason": "No ERP shipping method is configured for the matched carrier",
        }

    order = _order(db, salla_shipment)
    sales_document_id = None
    customer_name = _customer_name(db, order)
    if order:
        mapping = db.scalar(
            select(IntegrationMapping).where(
                IntegrationMapping.company_id == order.company_id,
                IntegrationMapping.connection_id == order.connection_id,
                IntegrationMapping.entity_type == "salla_order",
                IntegrationMapping.external_id == str(order.external_id),
            )
        )
        sales_document_id = mapping.local_id if mapping else None

    tracking = (
        salla_shipment.tracking_number
        or salla_shipment.shipping_number
        or f"SALLA-{salla_shipment.external_id}"
    )[:100]
    cod = Decimal(salla_shipment.cash_on_delivery or 0)
    fee = Decimal(salla_shipment.total or 0)
    target_status = _STATUS_MAP.get(
        str(salla_shipment.status or "").lower().replace(" ", "_"),
        "pending",
    )
    obj = Shipment(
        company_id=salla_shipment.company_id,
        carrier_id=carrier.id,
        method_id=method.id,
        sales_document_id=sales_document_id,
        tracking_no=tracking,
        status="pending",
        cod_amount=cod,
        shipping_fee=fee,
        customer_name=customer_name,
        notes=f"Imported from Salla shipment {salla_shipment.external_id}",
    )
    db.add(obj)
    db.flush()

    # A newly imported Salla shipment may arrive at a terminal/intermediate
    # state without its earlier webhooks. Replay the canonical ERP transition
    # path instead of mutating status directly, so status history and financial
    # events are generated exactly as for native ERP shipments.
    target_status = _advance_status(obj.status, target_status)
    canonical_path = [
        "preparing",
        "packing",
        "shipped",
        "in_transit",
        "delivering",
        "out_for_delivery",
        "delivered",
        "returning",
        "returned",
    ]
    if target_status == "cancelled":
        shipping_status_service.apply_transition(
            db, obj, "cancelled",
            changed_on=salla_shipment.created_at_salla.date() if salla_shipment.created_at_salla else None,
            user_id=_system_user_id(db, salla_shipment.company_id),
        )
    else:
        target_index = canonical_path.index(target_status) if target_status in canonical_path else -1
        if target_index >= 0:
            for status_code in canonical_path[: target_index + 1]:
                shipping_status_service.apply_transition(
                    db, obj, status_code,
                    changed_on=salla_shipment.created_at_salla.date() if salla_shipment.created_at_salla else None,
                    user_id=_system_user_id(db, salla_shipment.company_id),
                )
    db.add(
        IntegrationMapping(
            company_id=salla_shipment.company_id,
            connection_id=salla_shipment.connection_id,
            entity_type="salla_shipment",
            external_id=str(salla_shipment.external_id),
            local_id=obj.id,
        )
    )
    db.flush()
    return {"status": "created", "shipment_id": obj.id}


def sync_salla_shipments_for_order(db: Session, order: SallaOrder) -> list[dict]:
    rows = db.scalars(
        select(SallaShipment).where(
            SallaShipment.company_id == order.company_id,
            SallaShipment.connection_id == order.connection_id,
            SallaShipment.order_id == order.id,
        ).order_by(SallaShipment.id)
    ).all()
    return [sync_salla_shipment(db, row) for row in rows]
