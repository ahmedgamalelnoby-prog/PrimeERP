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


@router.post("/preview")
def preview_report(payload: ReportPayload) -> dict[str, Any]:
    if payload.format == "text":
        body = "\n".join(f"{key}: {value}" for key, value in payload.data.items())
    else:
        body = json.dumps(payload.data, ensure_ascii=False, indent=2, default=str)
    return {"title": payload.title, "format": payload.format, "body": body}


@router.post("/deliver")
def deliver_report(request: DeliveryRequest) -> dict[str, Any]:
    if request.channel == "email":
        _send_email(request.destination, request.title, request.body)
        return {"status": "sent", "channel": "email"}
    provider_reference = _send_whatsapp(request.destination, request.body)
    return {"status": "sent", "channel": "whatsapp", "provider_reference": provider_reference}
