from sqlalchemy.orm import Session

from .models import IntegrationEvent
from .salla_service import mark_event_failed, mark_event_processed, process_salla_event


def process_salla_event_id(db: Session, event_id: int) -> IntegrationEvent:
    """Process one stored Salla event transactionally.

    The current stage records the external mapping only. Domain creation is
    intentionally not inferred from arbitrary webhook payloads; provider
    adapters can attach internal IDs after canonical domain services create
    the corresponding records.
    """
    event = db.get(IntegrationEvent, event_id)
    if event is None:
        raise ValueError("Integration event not found")
    if event.status == "processed":
        return event

    try:
        process_salla_event(db, event)
        mark_event_processed(db, event.id)
        db.commit()
        db.refresh(event)
        return event
    except Exception as exc:
        db.rollback()
        event = db.get(IntegrationEvent, event_id)
        if event is None:
            raise
        mark_event_failed(db, event_id, str(exc))
        db.commit()
        db.refresh(event)
        raise
