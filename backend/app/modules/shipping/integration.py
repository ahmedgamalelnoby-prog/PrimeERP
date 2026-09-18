"""Provider-neutral shipping carrier mapping helpers."""
from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.modules.integrations.models import IntegrationMapping
from app.modules.shipping.models import ShippingCarrier

GENERIC_ENTITY_TYPE = "shipping_carrier"
LEGACY_ENTITY_TYPES = ("salla_shipping_company",)


def find_mapped_carrier(db: Session, *, company_id: int, connection_id: int, external_carrier_id: str) -> ShippingCarrier | None:
    value = str(external_carrier_id).strip()
    if not value:
        return None
    types = (GENERIC_ENTITY_TYPE, *LEGACY_ENTITY_TYPES)
    mapping = db.scalar(select(IntegrationMapping).where(
        IntegrationMapping.company_id == company_id,
        IntegrationMapping.connection_id == connection_id,
        IntegrationMapping.entity_type.in_(types),
        IntegrationMapping.external_id == value,
    ).order_by(IntegrationMapping.entity_type == GENERIC_ENTITY_TYPE, IntegrationMapping.id.desc()))
    if mapping is None:
        return None
    return db.scalar(select(ShippingCarrier).where(
        ShippingCarrier.id == mapping.local_id,
        ShippingCarrier.company_id == company_id,
        ShippingCarrier.is_active.is_(True),
    ))


def link_carrier(db: Session, *, company_id: int, connection_id: int, external_carrier_id: str, carrier_id: int) -> IntegrationMapping:
    carrier = db.scalar(select(ShippingCarrier).where(
        ShippingCarrier.id == carrier_id,
        ShippingCarrier.company_id == company_id,
        ShippingCarrier.is_active.is_(True),
    ))
    if carrier is None:
        raise ValueError("Shipping carrier does not belong to the company or is inactive")
    value = str(external_carrier_id).strip()
    if not value:
        raise ValueError("External carrier id is required")

    mapping = db.scalar(select(IntegrationMapping).where(
        IntegrationMapping.company_id == company_id,
        IntegrationMapping.connection_id == connection_id,
        IntegrationMapping.entity_type.in_((GENERIC_ENTITY_TYPE, *LEGACY_ENTITY_TYPES)),
        IntegrationMapping.external_id == value,
    ).order_by(IntegrationMapping.id.desc()))
    if mapping is None:
        mapping = IntegrationMapping(
            company_id=company_id,
            connection_id=connection_id,
            entity_type=GENERIC_ENTITY_TYPE,
            external_id=value,
            local_id=carrier.id,
        )
        db.add(mapping)
    else:
        mapping.entity_type = GENERIC_ENTITY_TYPE
        mapping.local_id = carrier.id
    db.flush()
    return mapping
