from __future__ import annotations

import hashlib
import hmac
import json
import os
from urllib.parse import urlencode

from fastapi import APIRouter, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_current_user
from app.database.session import get_db
from app.modules.identity.models import User

from .salla_public_app_models import SallaAppInstallation
from .salla_public_app_service import (
    SallaPublicAppError,
    consume_sso_ticket,
    handle_app_event,
    issue_sso_ticket,
)

router = APIRouter(prefix="/salla-app", tags=["Salla Public App"])


def _verify_app_webhook(raw_body: bytes, signature: str | None, strategy: str | None) -> None:
    secret = os.getenv("SALLA_APP_WEBHOOK_SECRET")
    if not secret:
        raise HTTPException(503, "SALLA_APP_WEBHOOK_SECRET is not configured")
    if not signature:
        raise HTTPException(401, "Missing Salla app webhook signature")
    strategy = (strategy or "Signature").strip().lower()
    if strategy == "token":
        valid = hmac.compare_digest(signature, secret)
    else:
        candidates = (
            hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest(),
            hashlib.sha256(secret.encode() + raw_body).hexdigest(),
            hashlib.sha256(raw_body + secret.encode()).hexdigest(),
        )
        valid = any(hmac.compare_digest(signature.lower(), candidate) for candidate in candidates)
    if not valid:
        raise HTTPException(401, "Invalid Salla app webhook signature")


@router.post("/webhook", status_code=202)
async def receive_salla_app_event(
    request: Request,
    x_salla_security_strategy: str | None = Header(default=None, alias="X-Salla-Security-Strategy"),
    x_salla_signature: str | None = Header(default=None, alias="X-Salla-Signature"),
):
    raw = await request.body()
    if len(raw) > 1_048_576:
        raise HTTPException(413, "Webhook payload is too large")
    _verify_app_webhook(raw, x_salla_signature, x_salla_security_strategy)
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(400, "Invalid Salla webhook JSON") from exc
    if not isinstance(payload, dict):
        raise HTTPException(422, "Webhook payload must be an object")
    db = next(get_db())
    try:
        result = handle_app_event(db, payload)
        return {"accepted": True, "result": result}
    except SallaPublicAppError as exc:
        db.rollback()
        raise HTTPException(502, str(exc)) from exc
    finally:
        db.close()


@router.get("/launch")
def launch_from_salla(
    current_user: User = __import__("fastapi").Depends(get_current_user),
    db: Session = __import__("fastapi").Depends(get_db),
):
    installation = db.scalar(
        select(SallaAppInstallation)
        .where(
            SallaAppInstallation.user_id == current_user.id,
            SallaAppInstallation.status == "active",
        )
        .order_by(SallaAppInstallation.id.desc())
    )
    if installation is None:
        raise HTTPException(404, "No active Salla installation is linked to this account")
    ticket = issue_sso_ticket(db, installation)
    frontend = os.getenv("PRIMEERP_FRONTEND_URL", "http://localhost:3000").rstrip("/")
    return {"redirect_url": f"{frontend}/salla/sso?{urlencode({'ticket': ticket})}", "expires_in": 120}


@router.post("/sso/exchange")
def exchange_sso_ticket(ticket: str, db: Session = __import__("fastapi").Depends(get_db)):
    if not ticket or len(ticket) > 128:
        raise HTTPException(400, "Invalid SSO ticket")
    try:
        token = consume_sso_ticket(db, ticket)
    except SallaPublicAppError as exc:
        db.rollback()
        raise HTTPException(401, str(exc)) from exc
    return {"access_token": token, "token_type": "bearer", "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60}
