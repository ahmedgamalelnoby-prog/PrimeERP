from __future__ import annotations

import hashlib
import json
import os
import secrets
import unicodedata
import re
from datetime import datetime, timedelta, timezone
from typing import Any

import requests
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token
from app.modules.companies.models import Company
from app.modules.identity.models import User
from app.modules.saas.models import Subscription, SubscriptionPlan, Tenant, TenantModule
from app.modules.saas.schemas import TenantRegistrationRequest
from app.modules.saas.service import register_trial_tenant, resolve_enabled_modules

from .models import IntegrationConnection, IntegrationEvent
from .salla_public_app_models import SallaAppEvent, SallaAppInstallation, SallaSSOTicket
from .salla_models import SallaOrder
from .salla_service import normalize_salla_event
from .salla_erp_finalize import finalize_salla_order
from .salla_shipping_service import sync_salla_shipment

SALLA_USER_INFO_URL = "https://accounts.salla.sa/oauth2/user/info"


class SallaPublicAppError(RuntimeError):
    """Raised when the Salla public-app handshake cannot be completed safely."""


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


def _event_id(payload: dict[str, Any]) -> str:
    for source in (payload, _payload_data(payload)):
        value = _text(source, "event_id", "event_idempotency_key", "id")
        if value:
            return value[:255]
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _event_payload_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


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
    existing = db.scalars(
        select(User).where(
            func.lower(User.email) == (email or "").lower(),
            User.is_deleted.is_(False),
        )
    ).all() if email else []
    if existing:
        raise SallaPublicAppError(
            "Salla merchant email already belongs to a PrimeERP account; explicit account linking is required"
        )

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
    connection = None
    if installation.connection_id:
        connection = db.scalar(
            select(IntegrationConnection)
            .join(Company, Company.id == IntegrationConnection.company_id)
            .where(
                IntegrationConnection.id == installation.connection_id,
                IntegrationConnection.company_id == installation.company_id,
                Company.tenant_id == installation.tenant_id,
                IntegrationConnection.provider == "salla",
                IntegrationConnection.is_active.is_(True),
            )
            .with_for_update()
        )
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
    installation.salla_user_id = _text(merchant, "user_id", "id")
    installation.status = "active"
    installation.store_name = _text(merchant, "name", "store_name", "business_name")
    installation.store_domain = _text(merchant, "domain", "store_url", "url")
    installation.merchant_email = _text(merchant, "email", "merchant_email", "owner_email")
    installation.metadata_json = merchant

    if db.scalar(
        select(Company.id).where(
            Company.id == installation.company_id,
            Company.tenant_id == installation.tenant_id,
            Company.is_active.is_(True),
        )
    ) is None:
        raise SallaPublicAppError("Salla installation company does not belong to its tenant")

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
    installation = db.scalar(select(SallaAppInstallation).where(SallaAppInstallation.connection_id == connection.id, SallaAppInstallation.company_id == connection.company_id, SallaAppInstallation.tenant_id == connection.tenant_id).with_for_update())
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


def _activate_primeerp_subscription(db: Session, installation: SallaAppInstallation, data: dict[str, Any]) -> None:
    try:
        mapping = json.loads(os.getenv("SALLA_PLAN_MAP_JSON", "{}"))
    except json.JSONDecodeError as exc:
        raise SallaPublicAppError("SALLA_PLAN_MAP_JSON is invalid") from exc

    candidates = [_text(data, "item_slug"), _text(data, "plan_name"), _text(data, "app_name")]
    plan_code = next((str(mapping.get(value)).strip() for value in candidates if value and mapping.get(value)), None)
    plan_code = plan_code or os.getenv("SALLA_DEFAULT_PLAN_CODE", "business").strip()
    plan = db.scalar(select(SubscriptionPlan).where(SubscriptionPlan.code == plan_code, SubscriptionPlan.is_active.is_(True)))
    if plan is None:
        raise SallaPublicAppError(f"PrimeERP subscription plan '{plan_code}' is not configured")

    external_id = _text(data, "subscription_id") or _text(data, "id")
    existing = db.scalar(select(Subscription).where(
        Subscription.tenant_id == installation.tenant_id,
        Subscription.external_provider == "salla",
        Subscription.external_subscription_id == external_id,
    )) if external_id else None

    start = datetime.now(timezone.utc)
    end = None
    for key, target in (("start_date", "start"), ("end_date", "end")):
        raw = _text(data, key)
        if raw:
            try:
                value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                if target == "start":
                    start = value
                else:
                    end = value
            except ValueError:
                pass

    if existing is None:
        existing = Subscription(
            tenant_id=installation.tenant_id,
            plan_id=plan.id,
            status="active",
            billing_cycle="monthly",
            starts_at=start,
            ends_at=end,
            trial_ends_at=None,
            next_billing_date=end,
            is_auto_renew=True,
            external_provider="salla",
            external_subscription_id=external_id,
            notes=f"Salla App Store plan: {_text(data, 'plan_name') or _text(data, 'item_slug') or plan.code}",
        )
        db.add(existing)
    else:
        existing.plan_id = plan.id
        existing.status = "active"
        existing.starts_at = start
        existing.ends_at = end
        existing.next_billing_date = end
        existing.is_auto_renew = True

    tenant = db.get(Tenant, installation.tenant_id)
    if tenant:
        tenant.status = "active"
        tenant.is_active = True
        tenant.is_trial = False
        tenant.trial_ends_at = None
        modules = resolve_enabled_modules(db, plan, tenant.business_type)
        enabled_ids = {module.id for module in modules}
        for module in modules:
            row = db.scalar(select(TenantModule).where(TenantModule.tenant_id == tenant.id, TenantModule.module_id == module.id))
            if row is None:
                db.add(TenantModule(tenant_id=tenant.id, module_id=module.id, is_enabled=True, starts_at=start, ends_at=end))
            else:
                row.is_enabled = True
                row.starts_at = row.starts_at or start
                row.ends_at = end
        if enabled_ids:
            stale = db.scalars(select(TenantModule).where(TenantModule.tenant_id == tenant.id, TenantModule.is_enabled.is_(True))).all()
            for row in stale:
                if row.module_id not in enabled_ids and row.ends_at is not None and row.ends_at <= start:
                    row.is_enabled = False


def _deactivate_primeerp_subscription(db: Session, installation: SallaAppInstallation, status: str) -> None:
    subscription = db.scalar(select(Subscription).where(
        Subscription.tenant_id == installation.tenant_id,
        Subscription.external_provider == "salla",
    ).order_by(Subscription.id.desc()))
    if subscription:
        subscription.status = status
        subscription.is_auto_renew = False
        if status == "canceled":
            subscription.cancelled_at = datetime.now(timezone.utc)
    tenant = db.get(Tenant, installation.tenant_id)
    if tenant and status in {"expired", "canceled"}:
        tenant.status = status
        tenant.is_active = True


def handle_app_event(db: Session, payload: dict[str, Any], event_id: str | None = None) -> dict[str, Any]:
    event = str(payload.get("event") or "").strip().lower()
    merchant_id = _merchant_id(payload)
    event_id = (event_id or _event_id(payload)).strip()[:255]
    payload_hash = _event_payload_hash(payload)

    installation = db.scalar(
        select(SallaAppInstallation)
        .where(SallaAppInstallation.merchant_id == merchant_id)
        .with_for_update()
    )

    event_row = db.scalar(
        select(SallaAppEvent)
        .where(
            SallaAppEvent.merchant_id == merchant_id,
            SallaAppEvent.event_id == event_id,
        )
        .with_for_update()
    )
    if event_row is not None:
        if event_row.payload_sha256 != payload_hash:
            raise SallaPublicAppError("Salla event id was already used with a different payload")
        if event_row.status == "processed":
            return {
                "accepted": True,
                "duplicate": True,
                "event_id": event_id,
                "result": event_row.result_json,
            }
        if event_row.status == "processing":
            raise SallaPublicAppError("Salla event is already being processed")
    else:
        try:
            with db.begin_nested():
                event_row = SallaAppEvent(
                    merchant_id=merchant_id,
                    event_id=event_id,
                    event_type=event,
                    payload_sha256=payload_hash,
                    status="processing",
                )
                db.add(event_row)
                db.flush()
        except IntegrityError:
            event_row = db.scalar(
                select(SallaAppEvent)
                .where(
                    SallaAppEvent.merchant_id == merchant_id,
                    SallaAppEvent.event_id == event_id,
                )
                .with_for_update()
            )
            if event_row is None:
                raise SallaPublicAppError("Unable to establish Salla event idempotency record")

    if event == "app.store.authorize":
        result = handle_authorize_event(db, payload)
        event_row.status = "processed"
        event_row.result_json = result
        event_row.processed_at = datetime.now(timezone.utc)
        db.commit()
        return result

    if installation is None:
        result = {"ignored": True, "reason": "installation_not_found", "event": event, "merchant_id": merchant_id}
    else:
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
                _deactivate_primeerp_subscription(db, installation, "expired")
            elif event == "app.subscription.canceled":
                installation.subscription_status = "canceled"
                _deactivate_primeerp_subscription(db, installation, "canceled")
            else:
                installation.subscription_status = event.rsplit(".", 1)[1]
                _deactivate_primeerp_subscription(db, installation, event.rsplit(".", 1)[1])
        elif event in {"app.trial.started", "app.subscription.started", "app.subscription.renewed"}:
            installation.status = "active"
            installation.subscription_status = "trialing" if event == "app.trial.started" else "active"
            if event in {"app.subscription.started", "app.subscription.renewed"} and _text(data, "item_type") in {None, "plan"}:
                _activate_primeerp_subscription(db, installation, data)
            installation.subscription_id = _text(data, "subscription_id", "id") or installation.subscription_id
            installation.subscription_item_slug = _text(data, "item_slug") or installation.subscription_item_slug
            installation.trial_ends_at = None
            if event == "app.trial.started":
                end = _text(data, "end_date")
                if end:
                    try:
                        installation.trial_ends_at = datetime.fromisoformat(end.replace("Z", "+00:00"))
                        tenant = db.get(Tenant, installation.tenant_id)
                        if tenant:
                            tenant.trial_ends_at = installation.trial_ends_at
                            tenant.status = "trial"
                            tenant.is_trial = True
                    except ValueError:
                        pass
        elif event == "app.updated":
            installation.status = "active"

        # Commerce webhooks cross the public-app boundary into the normalized
        # Salla tables and then use the existing ERP execution pipeline.
        elif event.startswith("order.") or event in {"order.created", "order.updated", "order.status.updated", "order.cancelled"}:
            if installation.connection_id is None:
                raise SallaPublicAppError("Salla installation has no active integration connection")
            connection = db.scalar(select(IntegrationConnection).where(
                IntegrationConnection.id == installation.connection_id,
                IntegrationConnection.company_id == installation.company_id,
                IntegrationConnection.provider == "salla",
                IntegrationConnection.is_active.is_(True),
            ))
            if connection is None:
                raise SallaPublicAppError("Salla integration connection is missing or inactive")
            normalized_event = IntegrationEvent(
                company_id=connection.company_id,
                connection_id=connection.id,
                external_event_id=event_id,
                event_type=event,
                payload=json.dumps(data, ensure_ascii=False),
            )
            counters = normalize_salla_event(db, normalized_event)
            external_order_id = _text(data, "id", "order_id")
            if not external_order_id:
                raise SallaPublicAppError(f"Salla {event} webhook does not contain an order id")
            order = db.scalar(select(SallaOrder).where(
                SallaOrder.company_id == connection.company_id,
                SallaOrder.connection_id == connection.id,
                SallaOrder.external_id == external_order_id,
            ).with_for_update())
            if order is None:
                raise SallaPublicAppError(f"Salla order {external_order_id} was not normalized")
            execution = finalize_salla_order(db, order)
            result = {
                "installation_id": installation.id,
                "event": event,
                "status": installation.status,
                "subscription_status": installation.subscription_status,
                "commerce": execution,
                "normalized": counters,
            }
        elif event.startswith("shipment.") or event in {"shipment.created", "shipment.updated", "shipment.status.updated"}:
            if installation.connection_id is None:
                raise SallaPublicAppError("Salla installation has no active integration connection")
            connection = db.scalar(select(IntegrationConnection).where(
                IntegrationConnection.id == installation.connection_id,
                IntegrationConnection.company_id == installation.company_id,
                IntegrationConnection.provider == "salla",
                IntegrationConnection.is_active.is_(True),
            ))
            if connection is None:
                raise SallaPublicAppError("Salla integration connection is missing or inactive")
            normalized_event = IntegrationEvent(
                company_id=connection.company_id,
                connection_id=connection.id,
                external_event_id=event_id,
                event_type=event,
                payload=json.dumps(data, ensure_ascii=False),
            )
            counters = normalize_salla_event(db, normalized_event)
            shipment_id = _text(data, "id", "shipment_id")
            shipment_result = None
            if shipment_id:
                from .salla_models import SallaShipment
                salla_shipment = db.scalar(select(SallaShipment).where(
                    SallaShipment.company_id == connection.company_id,
                    SallaShipment.connection_id == connection.id,
                    SallaShipment.external_id == shipment_id,
                ).with_for_update())
                if salla_shipment is None:
                    raise SallaPublicAppError(f"Salla shipment {shipment_id} was not normalized")
                shipment_result = sync_salla_shipment(db, salla_shipment)
            result = {
                "installation_id": installation.id,
                "event": event,
                "status": installation.status,
                "subscription_status": installation.subscription_status,
                "shipping": shipment_result,
                "normalized": counters,
            }
        result = locals().get("result") or {"installation_id": installation.id, "event": event, "status": installation.status, "subscription_status": installation.subscription_status}

    event_row.status = "processed"
    event_row.result_json = result
    event_row.processed_at = datetime.now(timezone.utc)
    db.commit()
    return result
