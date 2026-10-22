from __future__ import annotations

import re
import smtplib
import time
from datetime import datetime, timezone
from email.message import EmailMessage

import requests
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.context import get_effective_tenant_id
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.company_settings.service import get_company_setting
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.notifications.models import NotificationDelivery, NotificationGroup, NotificationGroupMember, NotificationTemplate
from app.modules.notifications.schemas import GroupUpsert, SendNotificationRequest, TemplateUpsert

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def _company(db: Session, company_id: int, user: User) -> Company:
    tenant_id = get_effective_tenant_id(user)
    if tenant_id is None:
        raise HTTPException(403, "User is not assigned to a tenant")
    company = db.scalar(select(Company).where(
        Company.id == company_id,
        Company.tenant_id == tenant_id,
        Company.is_active.is_(True),
    ))
    if company is None:
        raise HTTPException(404, "Active company not found in current tenant")
    return company


def _render(template: str, context: dict) -> str:
    return re.sub(
        r"\{\{\s*([A-Za-z0-9_.-]+)\s*\}\}",
        lambda match: str(context.get(match.group(1), "")),
        template,
    )


def _send_email(destination: str, title: str, body: str) -> str:
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


def _send_whatsapp(destination: str, body: str) -> str:
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


@router.get("/templates", dependencies=[Depends(require_permission("company.access"))])
def list_templates(
    company_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    company = _company(db, company_id, user)
    rows = db.scalars(select(NotificationTemplate).where(
        NotificationTemplate.company_id == company.id,
        NotificationTemplate.tenant_id == company.tenant_id,
    ).order_by(NotificationTemplate.channel, NotificationTemplate.code)).all()
    return [{"id": row.id, "code": row.code, "channel": row.channel, "title_template": row.title_template,
             "body_template": row.body_template, "is_active": row.is_active} for row in rows]


@router.put("/templates", dependencies=[Depends(require_permission("company.write"))])
def upsert_template(
    payload: TemplateUpsert,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    company = _company(db, payload.company_id, user)
    row = db.scalar(select(NotificationTemplate).where(
        NotificationTemplate.company_id == company.id,
        NotificationTemplate.code == payload.code,
        NotificationTemplate.channel == payload.channel,
    ).with_for_update())
    if row is None:
        row = NotificationTemplate(tenant_id=company.tenant_id, company_id=company.id, code=payload.code,
                                   channel=payload.channel, created_by=user.id)
        db.add(row)
    row.title_template = payload.title_template
    row.body_template = payload.body_template
    row.is_active = payload.is_active
    try:
        db.commit()
        db.refresh(row)
    except Exception:
        db.rollback()
        raise
    return {"id": row.id, "code": row.code, "channel": row.channel, "is_active": row.is_active}


@router.get("/groups", dependencies=[Depends(require_permission("company.write"))])
def list_groups(
    company_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    company = _company(db, company_id, user)
    groups = db.scalars(select(NotificationGroup).where(
        NotificationGroup.company_id == company.id,
        NotificationGroup.tenant_id == company.tenant_id,
    ).order_by(NotificationGroup.name)).all()
    result = []
    for group in groups:
        members = db.scalars(select(NotificationGroupMember).where(
            NotificationGroupMember.group_id == group.id,
        ).order_by(NotificationGroupMember.id)).all()
        result.append({"id": group.id, "code": group.code, "name": group.name, "channel": group.channel,
                       "is_active": group.is_active,
                       "members": [{"destination": m.destination, "label": m.label, "is_active": m.is_active} for m in members]})
    return result


@router.put("/groups", dependencies=[Depends(require_permission("company.write"))])
def upsert_group(
    payload: GroupUpsert,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    company = _company(db, payload.company_id, user)
    for member in payload.members:
        destination = member.destination.strip()
        if payload.channel == "email" and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", destination):
            raise HTTPException(422, "Each email group member must have a valid email destination")
        if payload.channel == "whatsapp" and not 8 <= len(re.sub(r"[^0-9]", "", destination)) <= 15:
            raise HTTPException(422, "Each WhatsApp group member must have a phone number with 8 to 15 digits")
    group = db.scalar(select(NotificationGroup).where(
        NotificationGroup.company_id == company.id,
        NotificationGroup.code == payload.code,
    ).with_for_update())
    if group is not None and group.channel != payload.channel:
        raise HTTPException(409, "An existing group code cannot change channel")
    if group is None:
        group = NotificationGroup(tenant_id=company.tenant_id, company_id=company.id, code=payload.code,
                                  name=payload.name, channel=payload.channel, created_by=user.id)
        db.add(group)
        db.flush()
    group.name = payload.name
    group.is_active = payload.is_active
    for member in db.scalars(select(NotificationGroupMember).where(NotificationGroupMember.group_id == group.id)).all():
        db.delete(member)
    for member in payload.members:
        db.add(NotificationGroupMember(group_id=group.id, destination=member.destination.strip(), label=member.label.strip()))
    try:
        db.commit()
        db.refresh(group)
    except Exception:
        db.rollback()
        raise
    return {"id": group.id, "code": group.code, "name": group.name, "channel": group.channel,
            "member_count": len(payload.members), "is_active": group.is_active}


@router.post("/send", status_code=202, dependencies=[Depends(require_permission("company.write"))])
def send_notification(
    payload: SendNotificationRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    company = _company(db, payload.company_id, user)
    if payload.channel == "email" and get_company_setting(db, company.id, "notifications.email_enabled") is not True:
        raise HTTPException(409, "Email delivery is disabled in company settings")
    if payload.channel == "whatsapp" and get_company_setting(db, company.id, "notifications.whatsapp_enabled") is not True:
        raise HTTPException(409, "WhatsApp delivery is disabled in company settings")
    retry_limit = int(get_company_setting(db, company.id, "notifications.retry_limit"))
    if payload.idempotency_key:
        existing = db.scalars(select(NotificationDelivery).where(
            NotificationDelivery.company_id == company.id,
            or_(NotificationDelivery.idempotency_key == payload.idempotency_key, NotificationDelivery.idempotency_key.like(payload.idempotency_key + ":%")),
        ).order_by(NotificationDelivery.id)).all()
        if existing:
            return {"status": "already_processed", "deliveries": [
                {"id": row.id, "channel": row.channel, "destination": row.destination, "status": row.status,
                 "provider_reference": row.provider_reference, "error_code": row.error_code} for row in existing
            ]}

    title, body = payload.title, payload.body
    if payload.template_code:
        template = db.scalar(select(NotificationTemplate).where(
            NotificationTemplate.company_id == company.id,
            NotificationTemplate.tenant_id == company.tenant_id,
            NotificationTemplate.code == payload.template_code,
            NotificationTemplate.channel == payload.channel,
            NotificationTemplate.is_active.is_(True),
        ))
        if template is None:
            raise HTTPException(404, "Active notification template not found")
        title = _render(template.title_template, payload.context)
        body = _render(template.body_template, payload.context)
    if not body.strip():
        raise HTTPException(422, "A non-empty body or active template is required")

    targets: list[tuple[str, int | None]] = []
    if payload.channel == "in_app":
        if payload.group_id is not None or payload.destination is not None:
            raise HTTPException(422, "In-app notifications are delivered to the current user only")
        targets.append((f"user:{user.id}", user.id))
    elif payload.group_id is not None:
        group = db.scalar(select(NotificationGroup).where(
            NotificationGroup.id == payload.group_id,
            NotificationGroup.company_id == company.id,
            NotificationGroup.tenant_id == company.tenant_id,
            NotificationGroup.is_active.is_(True),
        ))
        if group is None:
            raise HTTPException(404, "Active notification group not found")
        if group.channel != payload.channel:
            raise HTTPException(422, "Group channel does not match requested channel")
        members = db.scalars(select(NotificationGroupMember).where(
            NotificationGroupMember.group_id == group.id,
            NotificationGroupMember.is_active.is_(True),
        ).order_by(NotificationGroupMember.id)).all()
        targets.extend((member.destination, None) for member in members)
        if not targets:
            raise HTTPException(409, "Notification group has no active recipients")
    else:
        if not payload.destination:
            raise HTTPException(422, "A destination or group_id is required")
        targets.append((payload.destination.strip(), None))

    results = []
    for index, (destination, recipient_user_id) in enumerate(targets):
        key = payload.idempotency_key if len(targets) == 1 else (f"{payload.idempotency_key[:100]}:{index}" if payload.idempotency_key else None)
        row = NotificationDelivery(
            tenant_id=company.tenant_id, company_id=company.id, recipient_user_id=recipient_user_id,
            channel=payload.channel, destination=destination, title=title, body=body,
            status="queued", idempotency_key=key, created_by=user.id,
        )
        db.add(row)
        db.flush()
        provider_reference = None
        error_code = None
        try:
            if payload.channel == "in_app":
                provider_reference = "in_app"
            else:
                for attempt in range(retry_limit + 1):
                    try:
                        if payload.channel == "email":
                            if not re.fullmatch(r"[^\\s@]+@[^\\s@]+\\.[^\\s@]+", destination):
                                raise ValueError("invalid_email_destination")
                            provider_reference = _send_email(destination, title, body)
                        else:
                            provider_reference = _send_whatsapp(destination, body)
                        break
                    except (RuntimeError, ValueError, OSError, smtplib.SMTPException, requests.RequestException) as exc:
                        error_text = str(exc)
                        terminal = (
                            isinstance(exc, ValueError)
                            or "not_configured" in error_text
                            or "invalid_" in error_text
                            or re.search(r"provider_http_4\\d\\d", error_text) is not None
                            or attempt >= retry_limit
                        )
                        if terminal:
                            raise
                        time.sleep(min(2 ** attempt, 4))
            row.status = "sent"
            row.provider_reference = provider_reference
            row.sent_at = datetime.now(timezone.utc)
        except (RuntimeError, ValueError, OSError, smtplib.SMTPException, requests.RequestException) as exc:
            row.status = "failed"
            error_code = str(exc)[:80]
            row.error_code = error_code
        results.append(row)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"status": "completed", "count": len(results), "sent_count": sum(r.status == "sent" for r in results),
            "failed_count": sum(r.status == "failed" for r in results),
            "deliveries": [{"id": r.id, "channel": r.channel, "destination": r.destination, "status": r.status,
                            "provider_reference": r.provider_reference, "error_code": r.error_code} for r in results]}


@router.get("/inbox", dependencies=[Depends(require_permission("company.access"))])
def inbox(
    company_id: int = Query(..., gt=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    company = _company(db, company_id, user)
    rows = db.scalars(select(NotificationDelivery).where(
        NotificationDelivery.company_id == company.id,
        NotificationDelivery.tenant_id == company.tenant_id,
        NotificationDelivery.recipient_user_id == user.id,
        NotificationDelivery.channel == "in_app",
    ).order_by(NotificationDelivery.created_at.desc(), NotificationDelivery.id.desc()).limit(limit)).all()
    return [{"id": row.id, "title": row.title, "body": row.body, "status": row.status,
             "created_at": row.created_at, "sent_at": row.sent_at, "read_at": row.read_at} for row in rows]


@router.post("/{delivery_id}/read", dependencies=[Depends(require_permission("company.access"))])
def mark_read(
    delivery_id: int,
    company_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    company = _company(db, company_id, user)
    row = db.scalar(select(NotificationDelivery).where(
        NotificationDelivery.id == delivery_id,
        NotificationDelivery.company_id == company.id,
        NotificationDelivery.tenant_id == company.tenant_id,
        NotificationDelivery.recipient_user_id == user.id,
        NotificationDelivery.channel == "in_app",
    ).with_for_update())
    if row is None:
        raise HTTPException(404, "Notification not found")
    if row.read_at is None:
        row.read_at = datetime.now(timezone.utc)
        db.commit()
    return {"id": row.id, "read": True, "read_at": row.read_at}


@router.get("/deliveries", dependencies=[Depends(require_permission("company.write"))])
def list_deliveries(
    company_id: int = Query(..., gt=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    company = _company(db, company_id, user)
    rows = db.scalars(select(NotificationDelivery).where(
        NotificationDelivery.company_id == company.id,
        NotificationDelivery.tenant_id == company.tenant_id,
    ).order_by(NotificationDelivery.created_at.desc(), NotificationDelivery.id.desc()).limit(limit)).all()
    return [{"id": row.id, "channel": row.channel, "destination": row.destination, "title": row.title,
             "status": row.status, "provider_reference": row.provider_reference, "error_code": row.error_code,
             "created_at": row.created_at, "sent_at": row.sent_at} for row in rows]
