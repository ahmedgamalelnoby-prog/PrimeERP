from __future__ import annotations

import json
import smtplib
from email.message import EmailMessage
from typing import Any

import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings

router = APIRouter(prefix="/reports", tags=["reports"])


class ReportPayload(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    data: dict[str, Any]
    format: str = Field(default="json", pattern="^(json|text)$")


class DeliveryRequest(BaseModel):
    channel: str = Field(pattern="^(email|whatsapp)$")
    destination: str = Field(min_length=3, max_length=320)
    title: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1)


class AIAnalysisRequest(BaseModel):
    domain: str = Field(default="general", min_length=1, max_length=80)
    metrics: dict[str, Any]
    question: str | None = Field(default=None, max_length=2000)


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
    response = requests.post(
        url,
        headers={"Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}", "Content-Type": "application/json"},
        json={"messaging_product": "whatsapp", "to": destination, "type": "text", "text": {"body": body}},
        timeout=30,
    )
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
        return {**fallback, "engine": "prime_rules_v1", "ai_provider": "not_configured"}
    prompt = (
        "You are PrimeERP's financial/operational analyst. Analyze the supplied ERP metrics. "
        "Do not invent missing values. Return strict JSON with keys: executive_summary, risks, "
        "recommendations, questions_for_controller. Domain=" + request.domain + "\nMetrics=" +
        json.dumps(request.metrics, ensure_ascii=False, default=str) +
        ("\nQuestion=" + request.question if request.question else "")
    )
    try:
        response = requests.post(
            f"{settings.OPENAI_BASE_URL.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={"model": settings.AI_MODEL, "messages": [{"role": "user", "content": prompt}], "temperature": 0.1, "response_format": {"type": "json_object"}},
            timeout=60,
        )
        response.raise_for_status()
        body = response.json()
        content = body["choices"][0]["message"]["content"]
        return {"engine": "llm", "ai_provider": "openai_compatible", "analysis": json.loads(content), "rule_checks": fallback}
    except (requests.RequestException, KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        return {**fallback, "ai_provider": "fallback_after_provider_error", "provider_error": str(exc)[:500]}


@router.post("/preview")
def preview_report(payload: ReportPayload) -> dict[str, Any]:
    body = "\n".join(f"{key}: {value}" for key, value in payload.data.items()) if payload.format == "text" else json.dumps(payload.data, ensure_ascii=False, indent=2, default=str)
    return {"title": payload.title, "format": payload.format, "body": body}


@router.post("/deliver")
def deliver_report(request: DeliveryRequest) -> dict[str, Any]:
    if request.channel == "email":
        _send_email(request.destination, request.title, request.body)
        return {"status": "sent", "channel": "email"}
    return {"status": "sent", "channel": "whatsapp", "provider_reference": _send_whatsapp(request.destination, request.body)}


@router.post("/ai/analyze")
def analyze_report(request: AIAnalysisRequest) -> dict[str, Any]:
    return _ai_analysis(request)
