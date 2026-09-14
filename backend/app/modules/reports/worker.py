"""Small, DB-backed worker primitives for scheduled report delivery.

A deployment may run this function from a dedicated worker/cron process. It
never relies on in-memory schedules, and row locking prevents two workers
from claiming the same delivery at once.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.reports.models import ReportDelivery, ReportDeliveryAttempt


WORKER_ID = os.getenv("PRIMEERP_REPORT_WORKER_ID", "report-worker")


def claim_due_deliveries(db: Session, limit: int = 20) -> list[ReportDelivery]:
    now = datetime.now(timezone.utc)
    rows = list(db.scalars(
        select(ReportDelivery)
        .where(ReportDelivery.is_active.is_(True), ReportDelivery.next_run_at.is_not(None), ReportDelivery.next_run_at <= now)
        .order_by(ReportDelivery.next_run_at, ReportDelivery.id)
        .with_for_update(skip_locked=True)
        .limit(max(1, min(limit, 100)))
    ).all())
    return rows


def create_attempt(db: Session, delivery: ReportDelivery, status: str = "processing") -> ReportDeliveryAttempt:
    latest = db.scalar(
        select(ReportDeliveryAttempt)
        .where(ReportDeliveryAttempt.delivery_id == delivery.id)
        .order_by(ReportDeliveryAttempt.attempt_no.desc())
        .limit(1)
    )
    attempt_no = (latest.attempt_no if latest else 0) + 1
    attempt = ReportDeliveryAttempt(
        delivery_id=delivery.id,
        attempt_no=attempt_no,
        status=status,
        locked_at=datetime.now(timezone.utc),
        locked_by=WORKER_ID,
    )
    db.add(attempt)
    return attempt


def render_payload(definition, delivery: ReportDelivery) -> str:
    parameters = json.loads(definition.parameters_json or "{}")
    filters = json.loads(delivery.filters_json or "{}")
    if delivery.format == "text":
        lines = [f"Report: {definition.name}", f"Type: {definition.report_type}"]
        if parameters:
            lines.append(f"Parameters: {json.dumps(parameters, ensure_ascii=False, default=str)}")
        if filters:
            lines.append(f"Filters: {json.dumps(filters, ensure_ascii=False, default=str)}")
        return "\n".join(lines)
    return json.dumps({"report": definition.name, "report_type": definition.report_type, "parameters": parameters, "filters": filters}, ensure_ascii=False, default=str)
