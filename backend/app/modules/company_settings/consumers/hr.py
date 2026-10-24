from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.modules.company_settings.consumers.common import policy, require_policy_int


def attendance_source_allowed(db: Session, company_id: int, source: str) -> bool:
    """Whether an attendance write may enter through the configured source."""
    configured = policy(db, company_id, "hr.attendance_source")
    return source.strip().lower() == configured


def biometric_sync_due(
    db: Session,
    company_id: int,
    last_sync_at: datetime | None,
    *,
    now: datetime | None = None,
) -> bool:
    """Return whether the configured biometric polling interval has elapsed."""
    interval = require_policy_int(db, company_id, "hr.biometric_sync_interval_minutes", minimum=1)
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    if last_sync_at is None:
        return True
    previous = last_sync_at
    if previous.tzinfo is None:
        previous = previous.replace(tzinfo=timezone.utc)
    return current.astimezone(timezone.utc) >= previous.astimezone(timezone.utc) + timedelta(minutes=interval)
