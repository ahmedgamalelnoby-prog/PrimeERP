"""Provider-neutral shipping integration primitives.

A commerce adapter supplies an external carrier identity; this module maps it
to the single PrimeERP ShippingCarrier. The provider name is deliberately not
encoded into the core entity type.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.integrations.models import IntegrationMapping
from app.modules.shipping.models import ShippingCarrier


CARRIER_MAPPING_ENTITY = "shipping_carrier"


def find_mapped_carrier(
    db: Session,
    *,
    company_id: int,
    connection_id: int,
    external_carrier_id: str | None,
) -> ShippingCarrier | None:
    if not external_carrier_id:
        return None
    mapping = db.scalar(select(IntegrationMapping).where(
        IntegrationMapping.company_id == company_id,
        IntegrationMapping.connection_id == connection_id,
        IntegrationMapping.entity_type == CARRIER_MAPPING_ENTITY,
        IntegrationMapping.external_id == str(external_carrier_id),
    ))
    if not mapping:
        return None
    return db.scalar(select(ShippingCarrier).where(
        ShippingCarrier.id == mapping.local_id,
        ShippingCarrier.company_id == company_id,
        ShippingCarrier.is_active.is_(True),
    ))


def link_carrier(
    db: Session,
    *,
    company_id: int,
    connection_id: int,
    external_carrier_id: str,
    carrier_id: int,
) -> IntegrationMapping:
    mapping = db.scalar(select(IntegrationMapping).where(
        IntegrationMapping.company_id == company_id,
        IntegrationMapping.connection_id == connection_id,
        IntegrationMapping.entity_type == CARRIER_MAPPING_ENTITY,
        IntegrationMapping.external_id == str(external_carrier_id),
    ))
    if mapping:
        mapping.local_id = carrier_id
    else:
        mapping = IntegrationMapping(
            company_id=company_id,
            connection_id=connection_id,
            entity_type=CARRIER_MAPPING_ENTITY,
            external_id=str(external_carrier_id),
            local_id=carrier_id,
        )
        db.add(mapping)
    db.flush()
    return mapping
