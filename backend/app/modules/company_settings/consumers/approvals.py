from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable

from sqlalchemy.orm import Session

from app.modules.company_settings.consumers.common import policy, require_policy_bool, require_policy_int


def approval_mode(db: Session, company_id: int) -> str:
    """Return the configured approval semantics for the owning workflow."""
    mode = policy(db, company_id, "workflow.approval_mode")
    if mode not in {"sequential", "parallel", "any_one"}:
        raise ValueError(f"Unsupported approval mode: {mode!r}")
    return mode


def payroll_approval_required(db: Session, company_id: int) -> bool:
    return require_policy_bool(db, company_id, "hr.payroll_requires_approval")


def approval_escalation_due(
    db: Session,
    company_id: int,
    created_at: datetime,
    *,
    now: datetime | None = None,
) -> bool:
    """True when a still-pending approval has exceeded the company's SLA."""
    hours = require_policy_int(db, company_id, "workflow.escalation_after_hours", minimum=1)
    current = now or datetime.now(timezone.utc)
    created = created_at
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return current.astimezone(timezone.utc) >= created.astimezone(timezone.utc) + timedelta(hours=hours)


def approval_plan(mode: str, approver_ids: Iterable[int]) -> dict[str, object]:
    """Normalize approvers into a deterministic plan consumed by approval workflows."""
    ids = list(dict.fromkeys(approver_ids))
    if any(isinstance(user_id, bool) or not isinstance(user_id, int) or user_id <= 0 for user_id in ids):
        raise ValueError("Approver IDs must be positive integers")
    if mode not in {"sequential", "parallel", "any_one"}:
        raise ValueError(f"Unsupported approval mode: {mode!r}")
    if not ids:
        raise ValueError("At least one approver is required")
    return {
        "mode": mode,
        "approver_ids": ids,
        "required_approvals": 1 if mode == "any_one" else len(ids),
        "sequential": mode == "sequential",
    }
