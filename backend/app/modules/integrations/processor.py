"""Reliable integration event processing primitives.

The processor deliberately owns only the delivery state machine. Provider-specific
handlers can be registered by the application without making webhook ingestion
perform external API work synchronously.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import IntegrationEvent

MAX_ATTEMPTS = 10
BASE_RETRY_SECONDS = 2
MAX_RETRY_SECONDS = 300


class IntegrationProcessingError(RuntimeError):
    """Raised by a provider handler when an event cannot be processed."""


def _retry_delay(attempt: int) -> int:
    return min(MAX_RETRY_SECONDS, BASE_RETRY_SECONDS ** min(max(attempt, 1), 9))


def claim_next_event(db: Session, *, company_id: int | None = None) -> IntegrationEvent | None:
    """Atomically claim one due event for a worker transaction."""
    now = datetime.now(timezone.utc)
    stmt = (
        select(IntegrationEvent)
        .where(
            IntegrationEvent.status.in_(("received", "queued", "retrying")),
            (IntegrationEvent.next_attempt_at.is_(None)) | (IntegrationEvent.next_attempt_at <= now),
            IntegrationEvent.attempts < MAX_ATTEMPTS,
        )
        .order_by(IntegrationEvent.id)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    if company_id is not None:
        stmt = stmt.where(IntegrationEvent.company_id == company_id)
    event = db.scalar(stmt)
    if event is None:
        return None
    event.status = "processing"
    event.attempts += 1
    event.next_attempt_at = None
    db.flush()
    return event


def process_one(
    db: Session,
    *,
    handler: Callable[[IntegrationEvent], None],
    company_id: int | None = None,
) -> IntegrationEvent | None:
    """Claim and process one event, committing exactly once per outcome."""
    event = claim_next_event(db, company_id=company_id)
    if event is None:
        return None
    try:
        handler(event)
        event.status = "processed"
        event.processed_at = datetime.now(timezone.utc)
        event.last_error = None
        db.commit()
    except Exception as exc:
        db.rollback()
        event = db.scalar(select(IntegrationEvent).where(IntegrationEvent.id == event.id).with_for_update())
        if event is None:
            return None
        if event.attempts >= MAX_ATTEMPTS:
            event.status = "dead_letter"
            event.next_attempt_at = None
        else:
            event.status = "retrying"
            event.next_attempt_at = datetime.now(timezone.utc) + timedelta(seconds=_retry_delay(event.attempts))
        event.last_error = str(exc)[:4000]
        db.commit()
    return event
