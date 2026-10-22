from __future__ import annotations

from datetime import date, datetime

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
