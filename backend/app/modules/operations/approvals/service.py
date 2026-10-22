from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.company_settings.consumers.approvals import approval_plan
from app.modules.operations.approvals.models import ApprovalRequest, ApprovalStep


def create_approval_request(
    db: Session, *, tenant_id: int, company_id: int, requester_id: int,
    entity_type: str, entity_id: int | None, title: str, mode: str,
    approver_ids: list[int],
) -> ApprovalRequest:
    plan = approval_plan(mode, approver_ids)
    request = ApprovalRequest(
        tenant_id=tenant_id, company_id=company_id, entity_type=entity_type,
        entity_id=entity_id, title=title, requested_by_user_id=requester_id,
        mode=plan["mode"], status="pending",
    )
    db.add(request)
    db.flush()
    for index, approver_id in enumerate(plan["approver_ids"], start=1):
        db.add(ApprovalStep(
            request_id=request.id, approver_user_id=approver_id,
            sequence_no=index, status="pending",
        ))
    db.flush()
    return request


def decide_approval(
    db: Session, *, request: ApprovalRequest, actor_user_id: int,
    decision: str, reason: str | None,
) -> ApprovalRequest:
    if request.status != "pending":
        raise ValueError("Approval request is no longer pending")
    step = db.scalar(select(ApprovalStep).where(
        ApprovalStep.request_id == request.id,
        ApprovalStep.approver_user_id == actor_user_id,
        ApprovalStep.status == "pending",
    ).with_for_update())
    if step is None:
        raise PermissionError("No pending approval step is assigned to this user")

    if request.mode == "sequential":
        first_pending = db.scalar(select(ApprovalStep).where(
            ApprovalStep.request_id == request.id,
            ApprovalStep.status == "pending",
        ).order_by(ApprovalStep.sequence_no).with_for_update())
        if first_pending is None or first_pending.id != step.id:
            raise PermissionError("Sequential approvals must be decided in order")

    now = datetime.now(timezone.utc)
    step.status = "approved" if decision == "approve" else "rejected"
    step.decided_by_user_id = actor_user_id
    step.reason = reason
    step.decided_at = now

    pending_steps = list(db.scalars(select(ApprovalStep).where(
        ApprovalStep.request_id == request.id,
        ApprovalStep.status == "pending",
    ).order_by(ApprovalStep.sequence_no).with_for_update()).all())

    if decision == "reject":
        request.status = "rejected"
        request.decided_at = now
        for pending in pending_steps:
            pending.status = "skipped"
    elif request.mode == "any_one":
        request.status = "approved"
        request.decided_at = now
        for pending in pending_steps:
            pending.status = "skipped"
    elif not pending_steps:
        request.status = "approved"
        request.decided_at = now

    db.flush()
    return request
