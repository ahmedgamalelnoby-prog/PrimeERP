from __future__ import annotations

import hashlib
import secrets
import unicodedata
import re
from datetime import datetime, timedelta, timezone
from typing import Any

import requests
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token
from app.modules.companies.models import Company
from app.modules.identity.models import User
from app.modules.saas.schemas import TenantRegistrationRequest
from app.modules.saas.service import register_trial_tenant

from .models import IntegrationConnection
from .salla_public_app_models import SallaAppInstallation, SallaSSOTicket

SALLA_USER_INFO_URL = "https://accounts.salla.sa/oauth2/user/info"


class SallaPublicAppError(RuntimeError):
    pass


def _payload_data(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data")
    return data if isinstance(data, dict) else payload


def _text(data: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = data.get(key)
        if isinstance(value, dict):
            value = value.get("name") or value.get("value") or value.get("email") or value.get("id")
        if value not in (None, ""):
            return str(value).strip()
    return None


def _merchant_id(payload: dict[str, Any]) -> str:
    value = payload.get("merchant")
    if isinstance(value, dict):
        value = value.get("id") or value.get("merchant_id")
    if value is None:
        data = _payload_data(payload)
        value = data.get("merchant_id") or data.get("store_id") or data.get("id")
    if value is None:
        raise SallaPublicAppError("Salla authorization payload does not contain merchant id")
    return str(value)


def _encrypt(value: str | None) -> str | None:
    if not value:
        return None
    from cryptography.fernet import Fernet
    key = __import__("base64").urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode()).digest())
    return Fernet(key).encrypt(value.encode()).decode()


def decrypt_token(value: str | None) -> str | None:
    if not value:
        return None
    from cryptography.fernet import Fernet
    key = __import__("base64").urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode()).digest())
    return Fernet(key).decrypt(value.encode()).decode()


def _slug_seed(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-zA-Z0-9]+", "-", normalized.lower()).strip("-")[:60] or "salla-store"


def _unique_username(db: Session, email: str | None, merchant_id: str) -> str:
    seed = (email.split("@")[0] if email and "@" in email else f"salla_{merchant_id}")[:40]
    seed = re.sub(r"[^A-Za-z0-9_-]+", "_", seed.lower()).strip("_") or f"salla_{merchant_id}"
    candidate = seed
    suffix = 1
    while db.scalar(select(User.id).where(func.lower(User.username) == candidate.lower())) is not None:
        suffix += 1
        candidate = f"{seed[:40-len(str(suffix))-1]}_{suffix}"
    return candidate


def _fetch_merchant(access_token: str) -> dict[str, Any]:
    response = requests.get(
        SALLA_USER_INFO_URL,
        headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
        timeout=20,
    )
    if response.status_code >= 400:
        raise SallaPublicAppError(f"Salla merchant info request failed: {response.status_code}")
    payload = response.json()
    if not isinstance(payload, dict):
        raise SallaPublicAppError("Salla merchant info response is invalid")
    return _payload_data(payload)


def _provision_or_reuse_account(db: Session, merchant_id: str, merchant: dict[str, Any]) -> tuple[int, int, int]:
    email = _text(merchant, "email", "merchant_email", "owner_email")
    name = _text(merchant, "name", "store_name", "business_name") or f"Salla Store {merchant_id}"
    phone = _text(merchant, "mobile", "phone")
    language = "ar"
    existing = db.scalars(select(User).where(func.lower(User.email) == (email or "").lower(), User.is_deleted.is_(False))).all() if email else []
    if len(existing) == 1 and existing[0].tenant_id is not None:
        user = existing[0]
        company = db.scalar(select(Company).where(Company.tenant_id == user.tenant_id, Company.is_active.is_(True)).order_by(Company.id))
        if company is None:
            raise SallaPublicAppError("Existing PrimeERP tenant has no active company")
        return user.tenant_id, company.id, user.id

    if len(existing) > 1:
        raise SallaPublicAppError("Salla merchant email matches multiple PrimeERP accounts; manual linking is required")

    username = _unique_username(db, email, merchant_id)
    synthetic_email = email or f"salla-{merchant_id}@primeerp.local"
    registration = TenantRegistrationRequest(
        business_name=name[:200],
        business_type="retail",
        owner_name=(_text(merchant, "owner_name", "name") or name)[:150],
        email=synthetic_email,
        phone=phone,
        username=username,
        password=secrets.token_urlsafe(32)[:60],
        country_code="SA",
        language=language,
        company_name=name[:150],
        branch_name="Main Branch",
    )
    result = register_trial_tenant(db, registration)
    return result["tenant"].id, result["company"].id, result["user"].id


def _ensure_connection(db: Session, installation: SallaAppInstallation) -> IntegrationConnection:
    connection = db.scalar(select(IntegrationConnection).where(IntegrationConnection.id == installation.connection_id)) if installation.connection_id else None
    if connection is None:
        connection = IntegrationConnection(
            company_id=installation.company_id,
            provider="salla",
            name=f"Salla Public App #{installation.merchant_id}",
            base_url="https://api.salla.dev/admin/v2",
            credential_ref=None,
            webhook_secret_env="SALLA_APP_WEBHOOK_SECRET",
            is_active=True,
        )
        db.add(connection)
        db.flush()
        installation.connection_id = connection.id
    return connection


def handle_authorize_event(db: Session, payload: dict[str, Any]) -> dict[str, Any]:
    data = _payload_data(payload)
    access_token = _text(data, "access_token")
    refresh_token = _text(data, "refresh_token")
    if not access_token:
        raise SallaPublicAppError("Salla app.store.authorize did not include access_token")
    merchant_id = _merchant_id(payload)
    merchant = _fetch_merchant(access_token)

    installation = db.scalar(select(SallaAppInstallation).where(SallaAppInstallation.merchant_id == merchant_id).with_for_update())
    if installation is None:
        tenant_id, company_id, user_id = _provision_or_reuse_account(db, merchant_id, merchant)
        installation = SallaAppInstallation(
            merchant_id=merchant_id,
            tenant_id=tenant_id,
            company_id=company_id,
            user_id=user_id,
            access_token_ciphertext=_encrypt(access_token),
            refresh_token_ciphertext=_encrypt(refresh_token),
        )
        db.add(installation)
    else:
        installation.access_token_ciphertext = _encrypt(access_token) or installation.access_token_ciphertext
        if refresh_token:
            installation.refresh_token_ciphertext = _encrypt(refresh_token)

    expires = data.get("expires")
    if expires is not None:
        try:
            installation.token_expires_at = datetime.fromtimestamp(float(expires), tz=timezone.utc)
        except (TypeError, ValueError, OverflowError):
            installation.token_expires_at = datetime.now(timezone.utc) + timedelta(days=14)
    else:
        installation.token_expires_at = datetime.now(timezone.utc) + timedelta(days=14)
    installation.scope = _text(data, "scope")
    installation.token_type = _text(data, "token_type") or "bearer"
    installation.last_authorized_at = datetime.now(timezone.utc)
    installation.status = "active"
    installation.store_name = _text(merchant, "name", "store_name", "business_name")
    installation.store_domain = _text(merchant, "domain", "store_url", "url")
    installation.merchant_email = _text(merchant, "email", "merchant_email", "owner_email")
    installation.metadata_json = merchant

    connection = _ensure_connection(db, installation)
    connection.credential_ref = None
    connection.is_active = True
    db.commit()
    db.refresh(installation)
    return {
        "installation_id": installation.id,
        "merchant_id": merchant_id,
        "tenant_id": installation.tenant_id,
        "company_id": installation.company_id,
        "user_id": installation.user_id,
        "connection_id": connection.id,
        "status": installation.status,
    }


def issue_sso_ticket(db: Session, installation: SallaAppInstallation) -> str:
    if installation.user_id is None:
        raise SallaPublicAppError("Salla installation is not linked to a PrimeERP user")
    ticket = secrets.token_urlsafe(48)
    db.add(SallaSSOTicket(
        id=ticket,
        installation_id=installation.id,
        tenant_id=installation.tenant_id,
        user_id=installation.user_id,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=2),
    ))
    db.commit()
    return ticket


def consume_sso_ticket(db: Session, ticket: str) -> str:
    row = db.scalar(select(SallaSSOTicket).where(SallaSSOTicket.id == ticket).with_for_update())
    if row is None or row.consumed_at is not None:
        raise SallaPublicAppError("Invalid or already used Salla SSO ticket")
    now = datetime.now(timezone.utc)
    expires = row.expires_at if row.expires_at.tzinfo else row.expires_at.replace(tzinfo=timezone.utc)
    if expires <= now:
        raise SallaPublicAppError("Salla SSO ticket has expired")
    row.consumed_at = now
    token = create_access_token({"user_id": row.user_id, "sub": str(row.user_id), "tenant_id": row.tenant_id})
    db.commit()
    return token


def get_salla_access_token(db: Session, connection: IntegrationConnection) -> str:
    installation = db.scalar(select(SallaAppInstallation).where(SallaAppInstallation.connection_id == connection.id).with_for_update())
    if installation is None:
        raise SallaPublicAppError("Salla public-app installation not found")
    token = decrypt_token(installation.access_token_ciphertext)
    if not token:
        raise SallaPublicAppError("Salla access token is unavailable")
    expires = installation.token_expires_at
    if expires is not None:
        expires = expires if expires.tzinfo else expires.replace(tzinfo=timezone.utc)
        if expires <= datetime.now(timezone.utc) + timedelta(minutes=2):
            refresh = decrypt_token(installation.refresh_token_ciphertext)
            if not refresh:
                raise SallaPublicAppError("Salla access token expired and no refresh token is available")
            response = requests.post(
                "https://accounts.salla.sa/oauth2/token",
                data={"grant_type": "refresh_token", "refresh_token": refresh},
                timeout=20,
            )
            if response.status_code >= 400:
                raise SallaPublicAppError(f"Salla token refresh failed: {response.status_code}")
            data = response.json()
            new_token = _text(data, "access_token")
            if not new_token:
                raise SallaPublicAppError("Salla token refresh response did not include access_token")
            installation.access_token_ciphertext = _encrypt(new_token)
            new_refresh = _text(data, "refresh_token")
            if new_refresh:
                installation.refresh_token_ciphertext = _encrypt(new_refresh)
            expires_value = data.get("expires")
            installation.token_expires_at = (
                datetime.fromtimestamp(float(expires_value), tz=timezone.utc)
                if expires_value is not None
                else datetime.now(timezone.utc) + timedelta(days=14)
            )
            db.commit()
            token = new_token
    return token


def handle_app_event(db: Session, payload: dict[str, Any]) -> dict[str, Any]:
    event = str(payload.get("event") or "").strip().lower()
    merchant_id = _merchant_id(payload)
    installation = db.scalar(select(SallaAppInstallation).where(SallaAppInstallation.merchant_id == merchant_id).with_for_update())
    if event == "app.store.authorize":
        return handle_authorize_event(db, payload)
    if installation is None:
        return {"ignored": True, "reason": "installation_not_found", "event": event, "merchant_id": merchant_id}

    installation.last_webhook_at = datetime.now(timezone.utc)
    data = _payload_data(payload)
    if event in {"app.uninstalled", "app.subscription.expired", "app.subscription.canceled", "app.trial.expired", "app.trial.canceled"}:
        installation.status = "inactive" if event == "app.uninstalled" else "subscription_inactive"
        if event == "app.uninstalled":
            installation.subscription_status = "uninstalled"
            if installation.connection_id:
                connection = db.get(IntegrationConnection, installation.connection_id)
                if connection:
                    connection.is_active = False
        elif event == "app.subscription.expired":
            installation.subscription_status = "expired"
        elif event == "app.subscription.canceled":
            installation.subscription_status = "canceled"
        elif event in {"app.trial.expired", "app.trial.canceled"}:
            installation.subscription_status = event.rsplit(".", 1)[1]
    elif event in {"app.trial.started", "app.subscription.started", "app.subscription.renewed"}:
        installation.status = "active"
        installation.subscription_status = "trialing" if event == "app.trial.started" else "active"
        installation.subscription_id = _text(data, "subscription_id", "id") or installation.subscription_id
        installation.subscription_item_slug = _text(data, "item_slug") or installation.subscription_item_slug
        installation.trial_ends_at = None
        if event == "app.trial.started":
            end = _text(data, "end_date")
            if end:
                try:
                    installation.trial_ends_at = datetime.fromisoformat(end.replace("Z", "+00:00"))
                except ValueError:
                    pass
    elif event == "app.updated":
        installation.status = "active"
    db.commit()
    return {"installation_id": installation.id, "event": event, "status": installation.status, "subscription_status": installation.subscription_status}
