from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from .models import IntegrationEvent


def _retry_delay(attempts: int) -> int:
    """Return bounded exponential backoff in seconds."""
    attempts = max(1, int(attempts))
    return min(300, 2 ** attempts)


def claim_next_event(db: Session):
    """Atomically claim the next received/retryable integration event."""
    now = datetime.now(timezone.utc)
    stmt = (
        select(IntegrationEvent)
        .where(
            IntegrationEvent.status.in_(("received", "retry")),
            or_(IntegrationEvent.next_attempt_at.is_(None), IntegrationEvent.next_attempt_at <= now),
        )
        .order_by(IntegrationEvent.id)
        .with_for_update(skip_locked=True)
    )
    event = db.scalar(stmt)
    if event is None:
        return None
    event.status = "processing"
    event.attempts = int(event.attempts or 0) + 1
    event.next_attempt_at = None
    db.flush()
    return event


def mark_event_processed(db: Session, event: IntegrationEvent) -> IntegrationEvent:
    event.status = "processed"
    event.processed_at = datetime.now(timezone.utc)
    event.last_error = None
    event.next_attempt_at = None
    db.flush()
    return event


def mark_event_retry(db: Session, event: IntegrationEvent, error: str) -> IntegrationEvent:
    event.status = "retry"
    event.last_error = str(error)[:4000]
    event.next_attempt_at = datetime.now(timezone.utc) + timedelta(seconds=_retry_delay(event.attempts))
    db.flush()
    return event
