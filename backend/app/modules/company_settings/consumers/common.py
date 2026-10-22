from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.company_settings.service import get_company_setting


def policy(db: Session, company_id: int, key: str):
    """Read a typed policy value; unknown keys fail closed via the registry."""
    if company_id <= 0:
        raise ValueError("company_id must be a positive integer")
    return get_company_setting(db, company_id, key)


def require_policy_bool(db: Session, company_id: int, key: str) -> bool:
    value = policy(db, company_id, key)
    if not isinstance(value, bool):
        raise TypeError(f"Company setting {key} must be a boolean")
    return value


def require_policy_int(db: Session, company_id: int, key: str, *, minimum: int = 0) -> int:
    value = policy(db, company_id, key)
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise TypeError(f"Company setting {key} must be an integer >= {minimum}")
    return value
