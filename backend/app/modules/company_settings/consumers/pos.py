from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.company_settings.consumers.common import require_policy_bool


def cash_drawer_open_allowed(
    db: Session,
    company_id: int,
    *,
    linked_to_transaction: bool,
) -> bool:
    """Transaction-linked openings remain allowed; unlinked openings require an explicit policy."""
    if linked_to_transaction:
        return True
    return require_policy_bool(db, company_id, "pos.allow_open_cash_drawer")
