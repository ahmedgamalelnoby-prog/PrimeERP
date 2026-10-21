"""Durable scheduled-report worker.

The worker uses database leases, so multiple replicas can run safely. Report
providers are deliberately explicit: a schedule is never allowed to send a
fake "report" when its report type has no registered provider.
"""
from __future__ import annotations

import calendar
import json
import os
import smtplib
import time
import uuid
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from typing import Any, Callable

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.reports.models import ReportDelivery, ReportDeliveryAttempt, ReportDefinition

WORKER_ID = os.getenv("PRIMEERP_REPORT_WORKER_ID", f"report-worker-{uuid.uuid4().hex[:8]}")
LEASE_SECONDS = max(30, int(os.getenv("PRIMEERP_REPORT_WORKER_LEASE_SECONDS", "300")))
POLL_SECONDS = max(2, int(os.getenv("PRIMEERP_REPORT_WORKER_POLL_SECONDS", "10")))
MAX_ATTEMPTS = max(1, int(os.getenv("PRIMEERP_REPORT_MAX_ATTEMPTS", "5")))


class ReportProviderError(RuntimeError):
    pass


def _next_daily(now: datetime, hour: int, minute: int) -> datetime:
    candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return candidate if candidate > now else candidate + timedelta(days=1)


def _month_after(year: int, month: int, months: int) -> tuple[int, int]:
    month_index = year * 12 + month - 1 + months
    next_year, zero_based_month = divmod(month_index, 12)
    return next_year, zero_based_month + 1


def _monthly_occurrence(year: int, month: int, day: int, hour: int, minute: int) -> datetime:
    actual_day = min(day, calendar.monthrange(year, month)[1])
    return datetime(year, month, actual_day, hour, minute, tzinfo=timezone.utc)


def calculate_next_run(schedule: str, now: datetime | None = None) -> datetime:
    """Parse the supported durable schedule grammar in UTC.

    Supported forms: every:15m, every:2h, daily:09:00,
    weekly:MON@09:00, monthly:15@09:00 and quarterly:1@09:00.
    """
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    value = schedule.strip().lower()
    if value.startswith("every:"):
        token = value[6:]
        if len(token) < 2 or token[-1] not in "mhd":
            raise ValueError("Invalid every schedule; use every:15m, every:2h or every:1d")
        amount = int(token[:-1])
        if amount <= 0:
            raise ValueError("Schedule interval must be positive")
        return now + timedelta(**{"minutes" if token[-1] == "m" else "hours" if token[-1] == "h" else "days": amount})
    if value.startswith("daily:"):
        hour, minute = _parse_time(value[6:])
        return _next_daily(now, hour, minute)
    if value.startswith("weekly:"):
        day, raw_time = value[7:].split("@", 1)
        days = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
        if day not in days:
            raise ValueError("Weekly day must be MON..SUN")
        hour, minute = _parse_time(raw_time)
        delta = (days[day] - now.weekday()) % 7
        candidate = (now + timedelta(days=delta)).replace(hour=hour, minute=minute, second=0, microsecond=0)
        return candidate if candidate > now else candidate + timedelta(days=7)
    if value.startswith("monthly:") or value.startswith("quarterly:"):
        quarterly = value.startswith("quarterly:")
        raw_day, raw_time = value.split(":", 1)[1].split("@", 1)
        day = int(raw_day)
        hour, minute = _parse_time(raw_time)
        if not 1 <= day <= 31:
            raise ValueError("Schedule day must be between 1 and 31")
        if quarterly:
            quarter_start_month = ((now.month - 1) // 3) * 3 + 1
            candidate = _monthly_occurrence(now.year, quarter_start_month, day, hour, minute)
            if candidate <= now:
                year, month = _month_after(now.year, quarter_start_month, 3)
                candidate = _monthly_occurrence(year, month, day, hour, minute)
            return candidate
        candidate = _monthly_occurrence(now.year, now.month, day, hour, minute)
        if candidate <= now:
            year, month = _month_after(now.year, now.month, 1)
            candidate = _monthly_occurrence(year, month, day, hour, minute)
        return candidate
    raise ValueError("Unsupported schedule. Use every, daily, weekly, monthly or quarterly grammar")


def _parse_time(value: str) -> tuple[int, int]:
    parts = value.split(":")
    if len(parts) != 2:
        raise ValueError("Time must be HH:MM")
    hour, minute = int(parts[0]), int(parts[1])
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError("Time must be HH:MM")
    return hour, minute


def claim_due_deliveries(db: Session, limit: int = 20) -> list[ReportDelivery]:
    now = datetime.now(timezone.utc)
    rows = list(db.scalars(
        select(ReportDelivery)
        .where(
            ReportDelivery.is_active.is_(True),
            ReportDelivery.next_run_at.is_not(None),
            ReportDelivery.next_run_at <= now,
            (ReportDelivery.locked_until.is_(None) | (ReportDelivery.locked_until <= now)),
        )
        .order_by(ReportDelivery.next_run_at, ReportDelivery.id)
        .with_for_update(skip_locked=True)
        .limit(max(1, min(limit, 100)))
    ).all())
    lease_until = now + timedelta(seconds=LEASE_SECONDS)
    for row in rows:
        row.locked_until = lease_until
        row.locked_by = WORKER_ID
    db.commit()
    return rows


def create_attempt(db: Session, delivery: ReportDelivery, status: str = "processing") -> ReportDeliveryAttempt:
    latest = db.scalar(
        select(ReportDeliveryAttempt)
        .where(ReportDeliveryAttempt.delivery_id == delivery.id)
        .order_by(ReportDeliveryAttempt.attempt_no.desc())
        .limit(1)
    )
    attempt = ReportDeliveryAttempt(
        delivery_id=delivery.id,
        attempt_no=(latest.attempt_no if latest else 0) + 1,
        status=status,
        locked_at=datetime.now(timezone.utc),
        locked_by=WORKER_ID,
    )
    db.add(attempt)
    db.flush()
    return attempt


def _provider_snapshot(definition: ReportDefinition, delivery: ReportDelivery) -> dict[str, Any]:
    """Safe built-in provider used for health checks and manifest schedules."""
    return {
        "report_code": definition.code,
        "report_name": definition.name,
        "report_type": definition.report_type,
        "company_id": delivery.company_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "parameters": json.loads(definition.parameters_json or "{}"),
        "filters": json.loads(delivery.filters_json or "{}"),
    }


PROVIDERS: dict[str, Callable[[ReportDefinition, ReportDelivery], dict[str, Any]]] = {
    "snapshot": _provider_snapshot,
    "manifest": _provider_snapshot,
}


def render_payload(definition: ReportDefinition, delivery: ReportDelivery) -> str:
    provider = PROVIDERS.get(definition.report_type.lower())
    if provider is None:
        raise ReportProviderError(f"No report provider registered for report_type={definition.report_type!r}")
    payload = provider(definition, delivery)
    if delivery.format == "text":
        return "\n".join(f"{key}: {value}" for key, value in payload.items())
    return json.dumps(payload, ensure_ascii=False, default=str, indent=2)


def _send_email(destination: str, title: str, body: str) -> tuple[int, str]:
    if not settings.SMTP_HOST or not settings.SMTP_FROM:
        raise ReportProviderError("SMTP delivery is not configured")
    message = EmailMessage()
    message["From"], message["To"], message["Subject"] = settings.SMTP_FROM, destination, title
    message.set_content(body)
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as smtp:
        if settings.SMTP_STARTTLS:
            smtp.starttls()
        if settings.SMTP_USERNAME:
            smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        smtp.send_message(message)
    return 250, "smtp-accepted"


def _send_whatsapp(destination: str, body: str) -> tuple[int, str]:
    if not settings.WHATSAPP_ENABLED or not settings.WHATSAPP_ACCESS_TOKEN or not settings.WHATSAPP_PHONE_NUMBER_ID:
        raise ReportProviderError("WhatsApp delivery is not configured")
    url = f"{settings.WHATSAPP_API_BASE_URL.rstrip('/')}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    response = requests.post(url, headers={"Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}", "Content-Type": "application/json"}, json={"messaging_product": "whatsapp", "to": destination, "type": "text", "text": {"body": body}}, timeout=30)
    if response.status_code not in {200, 201}:
        raise ReportProviderError(f"WhatsApp provider rejected delivery: HTTP {response.status_code}")
    payload = response.json()
    messages = payload.get("messages") or []
    reference = str(messages[0].get("id")) if messages and isinstance(messages[0], dict) else "accepted"
    return response.status_code, reference


def process_delivery(db: Session, delivery: ReportDelivery) -> None:
    attempt = create_attempt(db, delivery)
    definition = db.get(ReportDefinition, delivery.report_definition_id)
    try:
        if definition is None or not definition.is_active or definition.company_id != delivery.company_id:
            raise ReportProviderError("Report definition is missing, inactive, or outside the delivery company")
        body = render_payload(definition, delivery)
        title = f"PrimeERP Report — {definition.name}"
        response_code, reference = _send_email(delivery.destination, title, body) if delivery.channel == "email" else _send_whatsapp(delivery.destination, body)
        now = datetime.now(timezone.utc)
        attempt.status = "success"
        attempt.response_code = response_code
        attempt.response_reference = reference
        delivery.last_run_at = now
        delivery.last_status = "success"
        delivery.last_error = None
        delivery.next_run_at = calculate_next_run(delivery.schedule, now)
    except Exception as exc:
        now = datetime.now(timezone.utc)
        attempt.status = "failed"
        attempt.error_message = str(exc)[:2000]
        delivery.last_run_at = now
        delivery.last_status = "dead_letter" if attempt.attempt_no >= MAX_ATTEMPTS else "failed"
        delivery.last_error = str(exc)[:2000]
        if attempt.attempt_no >= MAX_ATTEMPTS:
            delivery.is_active = False
        else:
            backoff = min(3600, 60 * (2 ** (attempt.attempt_no - 1)))
            delivery.next_run_at = now + timedelta(seconds=backoff)
    finally:
        delivery.locked_until = None
        delivery.locked_by = None
        db.commit()


def run_forever(session_factory: Callable[[], Session]) -> None:
    while True:
        db = session_factory()
        try:
            deliveries = claim_due_deliveries(db)
            for delivery in deliveries:
                process_delivery(db, delivery)
        finally:
            db.close()
        time.sleep(POLL_SECONDS)
