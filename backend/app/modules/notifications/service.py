from __future__ import annotations

import re
import smtplib
from email.message import EmailMessage

import requests

from app.core.config import settings


def render_template(template: str, context: dict) -> str:
    """Render only named {{ key }} tokens; never evaluate arbitrary expressions."""
    return re.sub(
        r"\{\{\s*([A-Za-z0-9_.-]+)\s*\}\}",
        lambda match: str(context.get(match.group(1), "")),
        template,
    )


def send_email(destination: str, title: str, body: str) -> str:
    if not settings.SMTP_HOST or not settings.SMTP_FROM:
        raise RuntimeError("email_not_configured")
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
    return "smtp_accepted"


def send_whatsapp(destination: str, body: str) -> str:
    if not settings.WHATSAPP_ENABLED or not settings.WHATSAPP_ACCESS_TOKEN or not settings.WHATSAPP_PHONE_NUMBER_ID:
        raise RuntimeError("whatsapp_not_configured")
    normalized = re.sub(r"[^0-9]", "", destination)
    if not 8 <= len(normalized) <= 15:
        raise ValueError("invalid_whatsapp_destination")
    url = f"{settings.WHATSAPP_API_BASE_URL.rstrip('/')}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    response = requests.post(
        url,
        headers={"Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}", "Content-Type": "application/json"},
        json={"messaging_product": "whatsapp", "to": normalized, "type": "text", "text": {"body": body}},
        timeout=30,
    )
    if response.status_code not in {200, 201}:
        raise RuntimeError(f"whatsapp_provider_http_{response.status_code}")
    payload = response.json()
    messages = payload.get("messages") or []
    return str(messages[0].get("id")) if messages and isinstance(messages[0], dict) else "provider_accepted"
