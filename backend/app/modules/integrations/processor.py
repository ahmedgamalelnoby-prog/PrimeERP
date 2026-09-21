from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from .models import IntegrationEvent

MAX_ATTEMPTS = 10
BASE_RETRY_SECONDS = 2
MAX_RETRY_SECONDS = 300
EVENT_RETRYABLE_STATES = ("received", "queued")


def _retry_delay(attempt: int) -> int:
    attempt = max(1, int(attempt))
    return min(MAX_RETRY_SECONDS, BASE_RETRY_SECONDS ** attempt)


def _failure_status(attempts: int) -> str:
    return "dead_letter" if int(attempts) >= MAX_ATTEMPTS else "queued"


def claim_next_event(db: Session, company_id: int | None = None, event_id: int | None = None) -> IntegrationEvent | None:
    now = datetime.now(timezone.utc)
    stmt = (
        select(IntegrationEvent)
        .where(
            IntegrationEvent.status.in_(EVENT_RETRYABLE_STATES),
            or_(IntegrationEvent.next_attempt_at.is_(None), IntegrationEvent.next_attempt_at <= now),
            IntegrationEvent.attempts < MAX_ATTEMPTS,
        )
        .order_by(IntegrationEvent.id)
        .with_for_update(skip_locked=True)
    )
    if company_id is not None:
        stmt = stmt.where(IntegrationEvent.company_id == company_id)
    if event_id is not None:
        stmt = stmt.where(IntegrationEvent.id == event_id)
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
    event.last_error = str(error)[:4000]
    event.status = _failure_status(event.attempts)
    event.next_attempt_at = (
        None
        if event.status == "dead_letter"
        else datetime.now(timezone.utc) + timedelta(seconds=_retry_delay(event.attempts))
    )
    db.flush()
    return event


def process_one(
    db: Session,
    handler: Callable[[IntegrationEvent], object],
    *,
    company_id: int | None = None,
    event_id: int | None = None,
) -> IntegrationEvent | None:
    event = claim_next_event(db, company_id=company_id, event_id=event_id)
    if event is None:
        return None
    claimed_id = event.id
    try:
        handler(event)
        mark_event_processed(db, event)
        db.commit()
        return event
    except Exception as exc:
        db.rollback()
        failed = db.scalar(select(IntegrationEvent).where(IntegrationEvent.id == claimed_id))
        if failed is None:
            raise
        # The claim increment was rolled back with the failed handler; restore it durably.
        failed.attempts = int(failed.attempts or 0) + 1
        mark_event_retry(db, failed, str(exc))
        db.commit()
        return failed
