from __future__ import annotations

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.orm import Session

from app.modules.company_settings.consumers.common import policy

_DATE_FORMATS = {
    "DD/MM/YYYY": "%d/%m/%Y",
    "MM/DD/YYYY": "%m/%d/%Y",
    "YYYY-MM-DD": "%Y-%m-%d",
}


def format_company_date(db: Session, company_id: int, value: date | datetime) -> str:
    """Format a date using the company's validated date-format preference."""
    configured = policy(db, company_id, "general.date_format")
    fmt = _DATE_FORMATS.get(configured)
    if fmt is None:
        # Fail closed rather than silently render dates in a misleading locale.
        raise ValueError(f"Unsupported company date format: {configured!r}")
    return value.strftime(fmt)


def company_clock_payload(now_utc: datetime, timezone_name: str) -> dict[str, str]:
    """Build a stable server-clock response using the company's IANA timezone."""
    if now_utc.tzinfo is None:
        raise ValueError("now_utc must be timezone-aware")
    try:
        company_tz = ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, TypeError) as exc:
        raise ValueError("Invalid company timezone") from exc
    normalized_utc = now_utc.astimezone(timezone.utc)
    return {
        "server_time_utc": normalized_utc.isoformat(),
        "company_timezone": timezone_name,
        "company_date": normalized_utc.astimezone(company_tz).date().isoformat(),
    }
