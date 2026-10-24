"""Periodic escalation worker for overdue company approval requests.

Run as a dedicated process with: python -m app.jobs.approval_escalation
Queues idempotent in-app reminders for the currently assigned approvers.
"""
from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

# Register every ORM model before this standalone worker configures SQLAlchemy mappers.
# The API process imports this registry during startup; workers must do so explicitly.
import app.database.models  # noqa: F401

from app.database.session import SessionLocal
from app.modules.company_settings.consumers.approvals import approval_escalation_due
from app.modules.companies.models import Company
from app.modules.notifications.models import NotificationDelivery
from app.modules.operations.approvals.models import ApprovalRequest, ApprovalStep

logger = logging.getLogger("primeerp.approval_escalation")


def process_due_approval_escalations(*, now: datetime | None = None) -> int:
    """Queue one reminder per pending approver/request once its configured SLA expires."""
    current = now or datetime.now(timezone.utc)
    queued = 0
    with SessionLocal() as db:
        requests = db.scalars(
            select(ApprovalRequest)
            .join(Company, Company.id == ApprovalRequest.company_id)
            .where(
                ApprovalRequest.status == "pending",
                Company.is_active.is_(True),
                Company.tenant_id == ApprovalRequest.tenant_id,
            )
            .order_by(ApprovalRequest.created_at, ApprovalRequest.id)
        ).all()
        for request in requests:
            try:
                if not approval_escalation_due(db, request.company_id, request.created_at, now=current):
                    continue
            except (ValueError, TypeError):
                logger.exception("Invalid escalation policy; request_id=%s", request.id)
                continue

            pending_steps = db.scalars(
                select(ApprovalStep).where(
                    ApprovalStep.request_id == request.id,
                    ApprovalStep.status == "pending",
                )
            ).all()
            for step in pending_steps:
                key = f"approval-escalation:{request.id}:{step.approver_user_id}"
                existing = db.scalar(
                    select(NotificationDelivery.id).where(
                        NotificationDelivery.company_id == request.company_id,
                        NotificationDelivery.idempotency_key == key,
                    )
                )
                if existing is not None:
                    continue
                delivery = NotificationDelivery(
                    tenant_id=request.tenant_id,
                    company_id=request.company_id,
                    recipient_user_id=step.approver_user_id,
                    channel="in_app",
                    destination=f"user:{step.approver_user_id}",
                    title="اعتماد متأخر يحتاج إلى متابعة",
                    body=(
                        f"طلب الاعتماد #{request.id} ({request.title}) ما زال معلقًا "
                        "وتجاوز مهلة الاعتماد المحددة للشركة."
                    ),
                    status="queued",
                    idempotency_key=key,
                )
                try:
                    with db.begin_nested():
                        db.add(delivery)
                        db.flush()
                    queued += 1
                except IntegrityError:
                    # Another worker may have inserted the same idempotency key.
                    logger.info("Duplicate escalation suppressed for %s", key)
        db.commit()
    return queued


def main() -> None:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    interval = max(30, int(os.getenv("APPROVAL_ESCALATION_POLL_SECONDS", "60")))
    logger.info("Approval escalation worker started; poll_interval=%s", interval)
    while True:
        try:
            queued = process_due_approval_escalations()
            if queued:
                logger.info("Queued %s overdue approval reminders", queued)
        except Exception:
            logger.exception("Approval escalation pass failed")
        time.sleep(interval)


if __name__ == "__main__":
    main()
