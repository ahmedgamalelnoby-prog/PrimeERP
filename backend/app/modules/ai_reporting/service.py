from __future__ import annotations

import csv
import io
import json
import os
import smtplib
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Any


@dataclass(frozen=True)
class DeliveryResult:
    ok: bool
    message_id: str | None = None
    error: str | None = None


class AIAnalysisService:
    """Provider-neutral AI analyst. No ERP write operations are exposed to the model."""

    def analyze(self, report_name: str, metrics: dict[str, Any], instructions: str | None = None) -> dict[str, Any]:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {
                "provider": "disabled",
                "model": os.getenv("AI_MODEL", "gpt-5.6-luna"),
                "summary": "AI provider is not configured. Set OPENAI_API_KEY to enable management analysis.",
                "insights": [],
                "recommendations": [],
            }

        model = os.getenv("AI_MODEL", "gpt-5.6-luna")
        prompt = {
            "report": report_name,
            "metrics": metrics,
            "instructions": instructions or "Analyze performance for management. Identify trends, anomalies, risks and concrete actions. Do not invent missing data.",
        }
        body = json.dumps({
            "model": model,
            "input": [
                {
                    "role": "system",
                    "content": "You are PrimeERP Management Intelligence. Analyze only the supplied ERP metrics. Return concise business insights and recommendations. Never claim to have changed ERP data.",
                },
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
            ],
        }).encode("utf-8")
        request = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=body,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            return {"provider": "openai", "model": model, "error": str(exc)}

        text = payload.get("output_text")
        if not text:
            parts: list[str] = []
            for item in payload.get("output", []):
                for content in item.get("content", []):
                    if content.get("type") in {"output_text", "text"} and content.get("text"):
                        parts.append(content["text"])
            text = "\n".join(parts).strip()
        return {"provider": "openai", "model": model, "summary": text or "No analysis returned."}


class ReportDeliveryService:
    def send_email(self, recipient: str, subject: str, body: str, attachment: tuple[str, bytes, str] | None = None) -> DeliveryResult:
        host = os.getenv("SMTP_HOST")
        port = int(os.getenv("SMTP_PORT", "587"))
        username = os.getenv("SMTP_USERNAME")
        password = os.getenv("SMTP_PASSWORD")
        sender = os.getenv("SMTP_FROM") or username
        if not host or not sender:
            return DeliveryResult(False, error="SMTP_HOST and SMTP_FROM/SMTP_USERNAME are required")

        message = EmailMessage()
        message["From"] = sender
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)
        if attachment:
            filename, content, mime = attachment
            maintype, subtype = mime.split("/", 1)
            message.add_attachment(content, maintype=maintype, subtype=subtype, filename=filename)
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(host, port, timeout=30) as smtp:
                if os.getenv("SMTP_STARTTLS", "true").lower() == "true":
                    smtp.starttls(context=context)
                if username:
                    smtp.login(username, password or "")
                smtp.send_message(message)
            return DeliveryResult(True)
        except (OSError, smtplib.SMTPException) as exc:
            return DeliveryResult(False, error=str(exc))

    def send_whatsapp(self, recipient: str, message: str) -> DeliveryResult:
        token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        graph_version = os.getenv("WHATSAPP_GRAPH_VERSION", "v23.0")
        if not token or not phone_number_id:
            return DeliveryResult(False, error="WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID are required")
        payload = json.dumps({
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": message[:4096]},
        }).encode("utf-8")
        request = urllib.request.Request(
            f"https://graph.facebook.com/{graph_version}/{phone_number_id}/messages",
            data=payload,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
            message_id = ((data.get("messages") or [{}])[0]).get("id")
            return DeliveryResult(True, message_id=message_id)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            return DeliveryResult(False, error=str(exc))


def rows_to_csv(rows: list[dict[str, Any]]) -> bytes:
    if not rows:
        return b""
    output = io.StringIO()
    fieldnames = list(dict.fromkeys(key for row in rows for key in row.keys()))
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8-sig")


ai_analysis_service = AIAnalysisService()
report_delivery_service = ReportDeliveryService()
