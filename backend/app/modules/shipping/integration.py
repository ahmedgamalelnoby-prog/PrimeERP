"""Provider-neutral shipping integration primitives.

The shipping module is currently a boundary adapter. Provider-specific shipping
models are imported lazily so the integration package remains import-safe while
the shipping domain is being completed independently.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.integrations.models import IntegrationMapping

if TYPE_CHECKING:
    from app.modules.shipping.models import ShippingCarrier

CARRIER_MAPPING_ENTITY = "shipping_carrier"


def find_mapped_carrier(
    db: Session,
    *,
    company_id: int,
    connection_id: int,
    external_carrier_id: str | None,
) -> "ShippingCarrier | None":
    if not external_carrier_id:
        return None
    from app.modules.shipping.models import ShippingCarrier

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
