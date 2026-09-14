from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.modules.identity.models import User
from app.modules.ai_reporting.models import ReportDeliveryLog, ReportSchedule
from app.modules.ai_reporting.service import ai_analysis_service, report_delivery_service, rows_to_csv

router = APIRouter(prefix="/ai-reporting", tags=["ai-reporting"])


REPORT_CATALOG = {
    "sales_performance": "Sales Performance",
    "cash_position": "Cash Position",
    "receivables_aging": "Receivables Aging",
    "inventory_performance": "Inventory Performance",
    "profitability": "Profitability / P&L",
    "tax_compliance": "Tax & Compliance",
    "management_summary": "AI Management Summary",
}


class AnalysisRequest(BaseModel):
    report_name: str = Field(min_length=1, max_length=160)
    metrics: dict[str, Any]
    instructions: str | None = Field(default=None, max_length=4000)


class ScheduleRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    report_key: str = Field(min_length=1, max_length=80)
    frequency: str = Field(default="monthly", pattern="^(daily|weekly|monthly|quarterly|custom)$")
    cron: str | None = Field(default=None, max_length=120)
    timezone: str = Field(default="Africa/Cairo", max_length=80)
    channels: list[str] = Field(default_factory=lambda: ["email"])
    recipients: list[str] = Field(default_factory=list)
    filters: dict[str, Any] = Field(default_factory=dict)
    format: str = Field(default="csv", pattern="^(csv|json)$")
    include_ai: bool = True
    next_run_at: datetime | None = None


class RunRequest(BaseModel):
    report_key: str
    title: str | None = None
    rows: list[dict[str, Any]] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    recipients: list[str] = Field(default_factory=list)
    channels: list[str] = Field(default_factory=lambda: ["email"])
    include_ai: bool = True


def _company_id(user: User) -> int:
    if user.tenant_id is None:
        raise HTTPException(status_code=403, detail="Authenticated user has no tenant context")
    # Company context is intentionally resolved by the existing ERP request context.
    # This module uses tenant_id as the isolation boundary until company selection is supplied.
    return int(user.tenant_id)


@router.get("/catalog")
def catalog(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    return {"success": True, "data": {"reports": [{"key": key, "name": name} for key, name in REPORT_CATALOG.items()]}}


@router.post("/analyze")
def analyze(request: AnalysisRequest, current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    return {"success": True, "data": ai_analysis_service.analyze(request.report_name, request.metrics, request.instructions)}


@router.post("/schedules")
def create_schedule(request: ScheduleRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    if request.report_key not in REPORT_CATALOG:
        raise HTTPException(status_code=400, detail="Unknown report_key")
    invalid_channels = set(request.channels) - {"email", "whatsapp"}
    if invalid_channels:
        raise HTTPException(status_code=400, detail=f"Unsupported channels: {sorted(invalid_channels)}")
    if not request.recipients:
        raise HTTPException(status_code=400, detail="At least one recipient is required")

    schedule = ReportSchedule(
        company_id=_company_id(current_user),
        name=request.name,
        report_key=request.report_key,
        frequency=request.frequency,
        cron=request.cron,
        timezone=request.timezone,
        channels=json.dumps(request.channels),
        recipients=json.dumps(request.recipients),
        filters=json.dumps(request.filters, ensure_ascii=False),
        format=request.format,
        include_ai=request.include_ai,
        next_run_at=request.next_run_at,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return {"success": True, "data": {"id": schedule.id, "name": schedule.name, "status": "active"}}


@router.get("/schedules")
def list_schedules(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    company_id = _company_id(current_user)
    schedules = db.query(ReportSchedule).filter(ReportSchedule.company_id == company_id).order_by(ReportSchedule.id.desc()).all()
    return {"success": True, "data": {"schedules": [
        {
            "id": item.id,
            "name": item.name,
            "report_key": item.report_key,
            "frequency": item.frequency,
            "timezone": item.timezone,
            "channels": json.loads(item.channels or "[]"),
            "recipients": json.loads(item.recipients or "[]"),
            "include_ai": item.include_ai,
            "is_active": item.is_active,
            "next_run_at": item.next_run_at.isoformat() if item.next_run_at else None,
            "last_run_at": item.last_run_at.isoformat() if item.last_run_at else None,
        } for item in schedules
    ]}}


@router.post("/run")
def run_report(request: RunRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    if request.report_key not in REPORT_CATALOG:
        raise HTTPException(status_code=400, detail="Unknown report_key")
    if not request.recipients:
        raise HTTPException(status_code=400, detail="At least one recipient is required")
    if set(request.channels) - {"email", "whatsapp"}:
        raise HTTPException(status_code=400, detail="Supported channels are email and whatsapp")

    company_id = _company_id(current_user)
    title = request.title or REPORT_CATALOG[request.report_key]
    analysis = ai_analysis_service.analyze(title, request.metrics) if request.include_ai else None
    summary = analysis.get("summary", "") if analysis else ""
    body = f"PrimeERP Report: {title}\n\n{summary}" if summary else f"PrimeERP Report: {title}\n"
    attachment = (f"{request.report_key}.csv", rows_to_csv(request.rows), "text/csv") if request.rows else None
    results = []
    now = datetime.now(timezone.utc)

    for channel in request.channels:
        for recipient in request.recipients:
            if channel == "email":
                result = report_delivery_service.send_email(recipient, f"PrimeERP - {title}", body, attachment)
            else:
                result = report_delivery_service.send_whatsapp(recipient, body)
            db.add(ReportDeliveryLog(
                company_id=company_id,
                report_key=request.report_key,
                channel=channel,
                recipient=recipient,
                status="sent" if result.ok else "failed",
                provider_message_id=result.message_id,
                error=result.error,
            ))
            results.append({"channel": channel, "recipient": recipient, "ok": result.ok, "message_id": result.message_id, "error": result.error})
    db.commit()
    return {"success": all(item["ok"] for item in results), "data": {"report_key": request.report_key, "generated_at": now.isoformat(), "analysis": analysis, "deliveries": results}}


@router.get("/deliveries")
def delivery_logs(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    company_id = _company_id(current_user)
    logs = db.query(ReportDeliveryLog).filter(ReportDeliveryLog.company_id == company_id).order_by(ReportDeliveryLog.id.desc()).limit(100).all()
    return {"success": True, "data": {"deliveries": [
        {"id": log.id, "report_key": log.report_key, "channel": log.channel, "recipient": log.recipient, "status": log.status, "error": log.error, "created_at": log.created_at.isoformat() if log.created_at else None}
        for log in logs
    ]}}
