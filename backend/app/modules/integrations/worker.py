"""Company-policy-driven automatic integration sync worker.

Only active Salla connections are polled. Each candidate is locked individually
and its claim timestamp is committed before network I/O. Manual sync requests
remain independently callable and are not serialized by this worker.
"""
from __future__ import annotations

import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.company_settings.consumers.integrations import integration_sync_due
from app.modules.integrations.models import IntegrationConnection
from app.modules.integrations.salla_sync import full_sync

logger = logging.getLogger(__name__)
WORKER_ID = os.getenv("PRIMEERP_INTEGRATION_WORKER_ID", f"integration-worker-{uuid.uuid4().hex[:8]}")
POLL_SECONDS = max(5, int(os.getenv("PRIMEERP_INTEGRATION_WORKER_POLL_SECONDS", "60")))
INTERVAL_MINUTES = max(1, int(os.getenv("PRIMEERP_INTEGRATION_SYNC_INTERVAL_MINUTES", "15")))


def claim_due_connection(db: Session, *, now: datetime | None = None) -> IntegrationConnection | None:
    """Claim one due connection without locking unrelated rows while checking policy."""
    current = now or datetime.now(timezone.utc)
    candidate_ids = db.scalars(
        select(IntegrationConnection.id)
        .where(
            IntegrationConnection.provider == "salla",
            IntegrationConnection.is_active.is_(True),
        )
        .order_by(IntegrationConnection.id)
    ).all()

    for connection_id in candidate_ids:
        # Lock exactly one candidate. SKIP LOCKED lets a peer worker claim a
        # different row instead of waiting on a row already being processed.
        connection = db.scalar(
            select(IntegrationConnection)
            .where(
                IntegrationConnection.id == connection_id,
                IntegrationConnection.provider == "salla",
                IntegrationConnection.is_active.is_(True),
            )
            .with_for_update(skip_locked=True)
        )
        if connection is None:
            db.rollback()
            continue

        if not integration_sync_due(
            db,
            connection.company_id,
            connection.last_sync_at,
            interval_minutes=INTERVAL_MINUTES,
            now=current,
        ):
            db.rollback()
            continue

        # Commit this claim before network I/O; a second worker then sees
        # the fresh timestamp and skips the same connection for this interval.
        connection.last_sync_at = current
        db.commit()
        db.refresh(connection)
        return connection

    db.rollback()
    return None


def run_once(session_factory: Callable[[], Session]) -> dict[str, int]:
    db = session_factory()
    claimed = None
    try:
        claimed = claim_due_connection(db)
    except Exception:
        db.rollback()
        logger.exception("Could not claim a due integration connection")
    finally:
        db.close()
    if claimed is None:
        return {"claimed": 0, "succeeded": 0, "failed": 0}

    db = session_factory()
    try:
        # Re-fetch under a fresh session; never hold the claim transaction over
        # external API calls. full_sync uses its own bounded HTTP timeouts.
        connection = db.scalar(
            select(IntegrationConnection).where(
                IntegrationConnection.id == claimed.id,
                IntegrationConnection.is_active.is_(True),
                IntegrationConnection.provider == "salla",
            )
        )
        if connection is None:
            return {"claimed": 1, "succeeded": 0, "failed": 0}
        full_sync(db, connection.id)
        logger.info("Automatic integration sync succeeded for connection_id=%s", connection.id)
        return {"claimed": 1, "succeeded": 1, "failed": 0}
    except Exception:
        db.rollback()
        logger.exception("Automatic integration sync failed for connection_id=%s", claimed.id)
        return {"claimed": 1, "succeeded": 0, "failed": 1}
    finally:
        db.close()


def run_forever(session_factory: Callable[[], Session]) -> None:
    logger.info(
        "PrimeERP integration sync worker started worker_id=%s interval_minutes=%s poll_seconds=%s",
        WORKER_ID, INTERVAL_MINUTES, POLL_SECONDS,
    )
    while True:
        run_once(session_factory)
        time.sleep(POLL_SECONDS)
