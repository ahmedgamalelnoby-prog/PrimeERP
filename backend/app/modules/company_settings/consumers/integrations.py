from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.modules.company_settings.consumers.common import require_policy_bool


def automatic_sync_enabled(db: Session, company_id: int) -> bool:
    return require_policy_bool(db, company_id, "integrations.auto_sync_enabled")


def integration_sync_due(
    db: Session,
    company_id: int,
    last_sync_at: datetime | None,
    *,
    interval_minutes: int,
    now: datetime | None = None,
) -> bool:
    """Gate a scheduled sync; interval is supplied by the integration's own schedule."""
    if not automatic_sync_enabled(db, company_id):
        return False
    if isinstance(interval_minutes, bool) or not isinstance(interval_minutes, int) or interval_minutes < 1:
        raise ValueError("interval_minutes must be an integer >= 1")
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    if last_sync_at is None:
        return True
    previous = last_sync_at
    if previous.tzinfo is None:
        previous = previous.replace(tzinfo=timezone.utc)
    return current.astimezone(timezone.utc) >= previous.astimezone(timezone.utc) + timedelta(minutes=interval_minutes)
