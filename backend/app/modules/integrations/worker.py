import logging
from collections.abc import Callable

from sqlalchemy.orm import Session

from .models import IntegrationEvent
from .salla_sync import process_salla_event_id

logger = logging.getLogger(__name__)


def process_one_due_event(db: Session, company_id: int | None = None) -> IntegrationEvent | None:
    """Process one due integration event.

    This is deliberately bounded to one event per invocation so it can be
    safely called by an external scheduler/worker without monopolising a DB
    transaction. Salla events use the transactional processor; unsupported
    providers remain queued for their provider adapter.
    """
    from datetime import datetime, timezone
    from sqlalchemy import select

    query = (
        select(IntegrationEvent)
        .where(
            IntegrationEvent.status.in_(["received", "queued", "retrying"]),
            IntegrationEvent.attempts < 10,
            (IntegrationEvent.next_attempt_at.is_(None) | (IntegrationEvent.next_attempt_at <= datetime.now(timezone.utc))),
        )
        .order_by(IntegrationEvent.id)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    if company_id is not None:
        query = query.where(IntegrationEvent.company_id == company_id)
    event = db.scalar(query)
    if event is None:
        return None
    provider = None
    from .models import IntegrationConnection
    connection = db.get(IntegrationConnection, event.connection_id)
    provider = connection.provider.lower() if connection else ""
    event.status = "processing"
    event.attempts += 1
    db.flush()
    if provider == "salla":
        db.commit()
        return process_salla_event_id(db, event.id)
    event.status = "retrying"
    event.last_error = f"No processor registered for provider: {provider or 'unknown'}"
    db.commit()
    return event
