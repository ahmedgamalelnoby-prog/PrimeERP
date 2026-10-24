from __future__ import annotations

import json
import smtplib
import uuid
from email.message import EmailMessage
from typing import Any

import requests
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.context import get_effective_tenant_id
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.saas.entitlements import require_module
from app.modules.reports.models import ReportDefinition, ReportDelivery
from app.modules.notifications.router import send_notification
from app.modules.notifications.schemas import SendNotificationRequest
from app.modules.accounting.reports.service import financial_report_service
from app.modules.reports.worker import PROVIDERS, calculate_next_run
from app.modules.platform.module_registry import REGISTRY_VERSION, knowledge_context

router = APIRouter(prefix="/reports", tags=["reports"], dependencies=[Depends(require_module("reports"))])


class ReportPayload(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    data: dict[str, Any]
    format: str = Field(default="json", pattern="^(json|text)$")


class DeliveryRequest(BaseModel):
    company_id: int = Field(gt=0)
    channel: str = Field(pattern="^(email|whatsapp)$")
    destination: str = Field(min_length=3, max_length=320)
    title: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1)


class ScheduleRequest(BaseModel):
    company_id: int = Field(gt=0)
    code: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    report_type: str = Field(default="manifest", pattern="^(snapshot|manifest)$", description="Use the metadata snapshot provider; live ERP report providers are not registered yet.")
    channel: str = Field(pattern="^(email|whatsapp)$")
    destination: str = Field(min_length=3, max_length=320)
    schedule: str = Field(min_length=1, max_length=120)
    format: str = Field(default="json", pattern="^(json|text)$")
    parameters: dict[str, Any] = Field(default_factory=dict)
    filters: dict[str, Any] = Field(default_factory=dict)


class AIAnalysisRequest(BaseModel):
    company_id: int = Field(gt=0)
    domain: str = Field(default="general", min_length=1, max_length=80)
    metrics: dict[str, Any] = Field(default_factory=dict)
    question: str | None = Field(default=None, max_length=2000)
    from_date: str | None = None
    to_date: str | None = None


def _company_for_user(db: Session, company_id: int, user: User) -> Company:
    tenant_id = get_effective_tenant_id(user)
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == tenant_id, Company.is_active.is_(True)))
    if company is None:
        raise HTTPException(403, "Company is outside the current tenant or inactive")
    return company


def _send_email(destination: str, title: str, body: str) -> None:
    if not settings.SMTP_HOST or not settings.SMTP_FROM:
        raise HTTPException(status_code=503, detail="SMTP delivery is not configured")
    message = EmailMessage()
    message["From"] = settings.SMTP_FROM
    message["To"] = destination
    message["Subject"] = title
    message.set_content(body)
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as smtp:
        if settings.SMTP_STARTTLS:
            smtp.starttls()
        if settings.SMTP_USERNAME:
            smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        smtp.send_message(message)


def _send_whatsapp(destination: str, body: str) -> str:
    if not settings.WHATSAPP_ENABLED or not settings.WHATSAPP_ACCESS_TOKEN or not settings.WHATSAPP_PHONE_NUMBER_ID:
        raise HTTPException(status_code=503, detail="WhatsApp delivery is not configured")
    url = f"{settings.WHATSAPP_API_BASE_URL.rstrip('/')}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    response = requests.post(url, headers={"Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}", "Content-Type": "application/json"}, json={"messaging_product": "whatsapp", "to": destination, "type": "text", "text": {"body": body}}, timeout=30)
    if response.status_code not in {200, 201}:
        raise HTTPException(status_code=502, detail=f"WhatsApp provider rejected delivery: HTTP {response.status_code}")
    payload = response.json()
    messages = payload.get("messages") or []
    return str(messages[0].get("id")) if messages and isinstance(messages[0], dict) else "accepted"


def _deterministic_analysis(metrics: dict[str, Any]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    numeric = {k: v for k, v in metrics.items() if isinstance(v, (int, float)) and not isinstance(v, bool)}
    if numeric.get("gross_margin_pct") is not None and numeric["gross_margin_pct"] < 15:
        findings.append({"severity": "high", "metric": "gross_margin_pct", "message": "Gross margin is below the 15% control threshold."})
    if numeric.get("overdue_ratio_pct") is not None and numeric["overdue_ratio_pct"] > 20:
        findings.append({"severity": "high", "metric": "overdue_ratio_pct", "message": "Overdue receivables exceed the 20% control threshold."})
    if numeric.get("inventory_turnover") is not None and numeric["inventory_turnover"] < 2:
        findings.append({"severity": "medium", "metric": "inventory_turnover", "message": "Inventory turnover is low and may indicate working-capital pressure."})
    if numeric.get("rejected_eta_documents") is not None and numeric["rejected_eta_documents"] > 0:
        findings.append({"severity": "high", "metric": "rejected_eta_documents", "message": "Rejected ETA documents require tax-compliance follow-up."})
    if numeric.get("cash_flow_gap") is not None and numeric["cash_flow_gap"] < 0:
        findings.append({"severity": "high", "metric": "cash_flow_gap", "message": "Projected cash flow is negative for the supplied period."})
    return {"engine": "prime_rules_v1", "risk_score": min(100, len(findings) * 20), "findings": findings, "recommendations": [f["message"] for f in findings]}


def _ai_analysis(request: AIAnalysisRequest) -> dict[str, Any]:
    fallback = _deterministic_analysis(request.metrics)
    if not settings.OPENAI_API_KEY:
        return {**fallback, "ai_provider": "not_configured", "knowledge_version": REGISTRY_VERSION}
    prompt = "You are PrimeERP's financial and operational analyst. Analyze only supplied live metrics and current module knowledge. Do not invent missing values, features, policies or implementation status. Return strict JSON with keys executive_summary, risks, recommendations, questions_for_controller. Knowledge version=" + REGISTRY_VERSION + " Modules=" + knowledge_context() + " Domain=" + request.domain + "\nMetrics=" + json.dumps(request.metrics, ensure_ascii=False, default=str) + ("\nQuestion=" + request.question if request.question else "")
    try:
        response = requests.post(f"{settings.OPENAI_BASE_URL.rstrip('/')}/chat/completions", headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}", "Content-Type": "application/json"}, json={"model": settings.AI_MODEL, "messages": [{"role": "user", "content": prompt}], "temperature": 0.1, "max_tokens": settings.AI_MAX_OUTPUT_TOKENS, "response_format": {"type": "json_object"}}, timeout=60)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return {"engine": "llm", "ai_provider": "openai_compatible", "knowledge_version": REGISTRY_VERSION, "analysis": json.loads(content), "rule_checks": fallback}
    except (requests.RequestException, KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        return {**fallback, "ai_provider": "fallback_after_provider_error", "knowledge_version": REGISTRY_VERSION, "provider_error": str(exc)[:500]}


@router.post("/preview")
def preview_report(payload: ReportPayload, current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    body = "\n".join(f"{key}: {value}" for key, value in payload.data.items()) if payload.format == "text" else json.dumps(payload.data, ensure_ascii=False, indent=2, default=str)
    return {"title": payload.title, "format": payload.format, "body": body}


@router.post("/deliver")
def deliver_report(request: DeliveryRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    _company_for_user(db, request.company_id, current_user)
    result = send_notification(
        SendNotificationRequest(
            company_id=request.company_id,
            channel=request.channel,
            destination=request.destination,
            title=request.title,
            body=request.body,
        ),
        db=db,
        user=current_user,
    )
    if result.get("failed_count", 0):
        raise HTTPException(status_code=502, detail="Report delivery failed; inspect notification delivery log")
    delivery = (result.get("deliveries") or [{}])[0]
    return {"status": "sent", "channel": request.channel, "provider_reference": delivery.get("provider_reference"),
            "delivery_id": delivery.get("id")}


@router.post("/schedules", status_code=201)
def create_schedule(request: ScheduleRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    _company_for_user(db, request.company_id, current_user)
    try:
        next_run = calculate_next_run(request.schedule)
    except (ValueError, TypeError) as exc:
        raise HTTPException(422, str(exc)) from exc
    definition = db.scalar(select(ReportDefinition).where(ReportDefinition.company_id == request.company_id, ReportDefinition.code == request.code))
    if definition is None:
        definition = ReportDefinition(company_id=request.company_id, code=request.code, name=request.name, report_type=request.report_type, parameters_json=json.dumps(request.parameters, ensure_ascii=False))
        db.add(definition)
        db.flush()
    elif not definition.is_active:
        raise HTTPException(409, "Report definition is inactive")
    elif definition.report_type.lower() not in PROVIDERS:
        raise HTTPException(409, "Report definition has no registered provider")
    elif definition.report_type.lower() != request.report_type.lower():
        raise HTTPException(409, "Report code already exists with a different report type")
    delivery = ReportDelivery(company_id=request.company_id, report_definition_id=definition.id, channel=request.channel, destination=request.destination, schedule=request.schedule, format=request.format, filters_json=json.dumps(request.filters, ensure_ascii=False), next_run_at=next_run, delivery_key=uuid.uuid4().hex)
    db.add(delivery)
    db.commit()
    db.refresh(delivery)
    return {"id": delivery.id, "report_definition_id": definition.id, "next_run_at": delivery.next_run_at, "status": "scheduled"}


@router.get("/schedules")
def list_schedules(company_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    return list(db.scalars(select(ReportDelivery).where(ReportDelivery.company_id == company_id).order_by(ReportDelivery.id.desc()).limit(500)).all())


@router.post("/ai/analyze", dependencies=[Depends(require_permission("accounting.access"))])
def analyze_report(
    request: AIAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    _company_for_user(db, request.company_id, current_user)
    from datetime import date

    try:
        from_date = date.fromisoformat(request.from_date) if request.from_date else None
        to_date = date.fromisoformat(request.to_date) if request.to_date else None
    except ValueError as exc:
        raise HTTPException(422, "from_date and to_date must use YYYY-MM-DD") from exc
    if from_date and to_date and from_date > to_date:
        raise HTTPException(422, "from_date cannot be after to_date")

    summary = financial_report_service.financial_summary(
        db,
        tenant_id=get_effective_tenant_id(current_user),
        company_id=request.company_id,
        from_date=from_date,
        to_date=to_date,
    )
    actual_metrics = {
        "revenue": float(summary.revenue),
        "expenses": float(summary.expenses),
        "net_profit": float(summary.net_profit),
        "assets": float(summary.assets),
        "liabilities": float(summary.liabilities),
        "equity": float(summary.equity),
    }
    if actual_metrics["revenue"]:
        actual_metrics["net_margin_pct"] = round(actual_metrics["net_profit"] / actual_metrics["revenue"] * 100, 2)
    # Keep caller-supplied context useful to the analysis without letting it
    # replace figures calculated from the tenant-scoped accounting records.
    supplemental_metrics = {key: value for key, value in request.metrics.items() if key not in actual_metrics}
    analysis_metrics = {**supplemental_metrics, **actual_metrics}
    enriched = AIAnalysisRequest(
        company_id=request.company_id,
        domain=request.domain,
        metrics=analysis_metrics,
        question=request.question,
        from_date=request.from_date,
        to_date=request.to_date,
    )
    result = _ai_analysis(enriched)
    result["company_id"] = request.company_id
    result["period"] = {"from_date": request.from_date, "to_date": request.to_date}
    result["actual_financial_metrics"] = actual_metrics
    return result
