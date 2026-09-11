import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .models import IntegrationConnection, IntegrationEvent
from .salla_models import SallaExternalMapping


SUPPORTED_ENTITY_TYPES = {"customer", "product", "order", "shipment"}


def upsert_mapping(
    db: Session,
    *,
    connection: IntegrationConnection,
    entity_type: str,
    external_id: str,
    internal_id: int | None = None,
    external_version: str | None = None,
    payload: dict | None = None,
) -> SallaExternalMapping:
    """Create/update an idempotent Salla external-to-internal mapping."""
    entity_type = entity_type.strip().lower()
    external_id = external_id.strip()
    if entity_type not in SUPPORTED_ENTITY_TYPES:
        raise ValueError("Unsupported Salla entity type")
    if not external_id:
        raise ValueError("Salla external_id is required")

    mapping = db.scalar(
        select(SallaExternalMapping)
        .where(
            SallaExternalMapping.connection_id == connection.id,
            SallaExternalMapping.entity_type == entity_type,
            SallaExternalMapping.external_id == external_id,
        )
        .with_for_update()
    )
    serialized = json.dumps(payload, ensure_ascii=False) if payload is not None else None
    if mapping is None:
        mapping = SallaExternalMapping(
            company_id=connection.company_id,
            connection_id=connection.id,
            entity_type=entity_type,
            external_id=external_id,
            internal_id=internal_id,
            external_version=external_version,
            payload=serialized,
            is_active=True,
        )
        db.add(mapping)
    else:
        if internal_id is not None:
            mapping.internal_id = internal_id
        if external_version is not None:
            mapping.external_version = external_version
        if serialized is not None:
            mapping.payload = serialized
        mapping.is_active = True
    db.flush()
    return mapping


def resolve_mapping(
    db: Session,
    *,
    connection_id: int,
    entity_type: str,
    external_id: str,
) -> SallaExternalMapping | None:
    return db.scalar(
        select(SallaExternalMapping).where(
            SallaExternalMapping.connection_id == connection_id,
            SallaExternalMapping.entity_type == entity_type.strip().lower(),
            SallaExternalMapping.external_id == external_id.strip(),
            SallaExternalMapping.is_active.is_(True),
        )
    )


def process_salla_event(db: Session, event: IntegrationEvent) -> SallaExternalMapping | None:
    """Persist the event's entity identity without guessing business records.

    Actual customer/product/order creation is intentionally delegated to the
    domain modules once their canonical creation services are available.
    """
    if event.status == "processed":
        return None
    connection = db.get(IntegrationConnection, event.connection_id)
    if connection is None or connection.provider.lower() != "salla":
        raise ValueError("Salla integration connection not found")

    try:
        payload = json.loads(event.payload)
    except (TypeError, ValueError) as exc:
        raise ValueError("Stored Salla event payload is invalid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("Stored Salla event payload must be an object")

    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    external_id = data.get("id") or data.get("order_id") or data.get("product_id") or data.get("customer_id")
    event_name = event.event_type.lower()
    if not external_id:
        raise ValueError("Salla event does not contain an entity id")

    if "order" in event_name:
        entity_type = "order"
    elif "product" in event_name:
        entity_type = "product"
    elif "customer" in event_name:
        entity_type = "customer"
    elif "shipment" in event_name:
        entity_type = "shipment"
    else:
        raise ValueError(f"Unsupported Salla event type: {event.event_type}")

    return upsert_mapping(
        db,
        connection=connection,
        entity_type=entity_type,
        external_id=str(external_id),
        payload=payload,
    )


def mark_event_processed(db: Session, event_id: int) -> IntegrationEvent:
    event = db.scalar(select(IntegrationEvent).where(IntegrationEvent.id == event_id).with_for_update())
    if event is None:
        raise ValueError("Integration event not found")
    event.status = "processed"
    event.processed_at = datetime.now(timezone.utc)
    event.next_attempt_at = None
    event.last_error = None
    db.flush()
    return event


def mark_event_failed(db: Session, event_id: int, error: str) -> IntegrationEvent:
    event = db.scalar(select(IntegrationEvent).where(IntegrationEvent.id == event_id).with_for_update())
    if event is None:
        raise ValueError("Integration event not found")
    event.status = "retrying" if event.attempts < 10 else "dead_letter"
    event.last_error = error[:4000]
    db.flush()
    return event
