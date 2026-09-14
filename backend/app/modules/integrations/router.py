import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.saas.entitlements import require_module
from .models import IntegrationConnection, IntegrationEvent
from .schemas import ConnectionCreate, ConnectionResponse, WebhookEventCreate
from .salla_models import SallaCustomer, SallaInvoice, SallaOrder, SallaOrderItem, SallaProduct, SallaProductVariant, SallaShipment
from .salla_service import normalize_salla_event
from .salla_sync import full_sync
from .salla_erp_finalize import finalize_salla_order
from .salla_shipping_service import sync_salla_shipment

MAX_WEBHOOK_BODY_BYTES = 1_048_576
router = APIRouter(prefix="/integrations", tags=["Integrations"], dependencies=[Depends(require_permission("integrations.access")), Depends(require_module("integrations"))])
public_router = APIRouter(prefix="/integrations", tags=["Integrations Webhooks"])

def _company_for_user(db: Session, company_id: int, user: User):
    if user.tenant_id is None: raise HTTPException(403, "User is not assigned to a tenant")
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == user.tenant_id))
    if company is None: raise HTTPException(403, "Company is outside the current tenant")
    return company

def _get_salla_connection(db: Session, connection_id: int):
    connection = db.scalar(select(IntegrationConnection).join(Company, Company.id == IntegrationConnection.company_id).where(IntegrationConnection.id == connection_id, IntegrationConnection.provider == "salla", IntegrationConnection.is_active.is_(True)))
    if connection is None: raise HTTPException(404, "Salla connection not found")
    return connection

def _verify_salla_signature(connection: IntegrationConnection, raw_body: bytes, strategy: str | None, signature: str | None) -> None:
    if not signature: raise HTTPException(401, "Missing Salla webhook signature")
    env_name = connection.webhook_secret_env
    if not env_name: raise HTTPException(503, "Salla webhook secret is not configured")
    secret = os.getenv(env_name)
    if not secret: raise HTTPException(503, "Salla webhook secret environment variable is unavailable")
    strategy = (strategy or "Signature").strip().lower()
    if strategy == "token": valid = hmac.compare_digest(signature, secret)
    else:
        candidates = (hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest(), hashlib.sha256(secret.encode() + raw_body).hexdigest(), hashlib.sha256(raw_body + secret.encode()).hexdigest())
        valid = any(hmac.compare_digest(signature.lower(), candidate) for candidate in candidates)
    if not valid: raise HTTPException(401, "Invalid Salla webhook signature")

def _event_identity(payload: dict, event_header: str | None, event_id_header: str | None, raw_body: bytes):
    external_event_id = event_id_header or payload.get("id") or payload.get("event_id")
    event_type = event_header or payload.get("event") or payload.get("event_type") or payload.get("type")
    if not event_type: raise HTTPException(422, "Salla webhook event type is required")
    if not external_event_id:
        event_digest = hashlib.sha256(str(event_type).encode() + b"\n" + raw_body).hexdigest()
        external_event_id = f"sha256:{event_digest}"
    return str(external_event_id), str(event_type)

def _process_event(db: Session, event: IntegrationEvent) -> dict:
    try:
        result = normalize_salla_event(db, event)
        event_key = event.event_type.lower().replace("_", ".")
        if event_key.startswith("order"):
            payload = json.loads(event.payload) if isinstance(event.payload, str) else event.payload
            data = payload.get("data", payload) if isinstance(payload, dict) else {}
            order_id = data.get("id") or data.get("order_id")
            if order_id is not None:
                order = db.scalar(select(SallaOrder).where(SallaOrder.connection_id == event.connection_id, SallaOrder.external_id == str(order_id)))
                if order: result["erp"] = finalize_salla_order(db, order)
        elif event_key.startswith("shipment") or "shipment." in event_key:
            payload = json.loads(event.payload) if isinstance(event.payload, str) else event.payload
            data = payload.get("data", payload) if isinstance(payload, dict) else {}
            shipment_id = data.get("id") or data.get("shipment_id")
            if shipment_id is not None:
                shipment = db.scalar(select(SallaShipment).where(SallaShipment.connection_id == event.connection_id, SallaShipment.external_id == str(shipment_id)))
                if shipment: result["erp_shipping"] = sync_salla_shipment(db, shipment)
        event.status = "processed"; event.processed_at = datetime.now(timezone.utc); event.last_error = None; db.commit(); return result
    except Exception as exc:
        db.rollback(); failed = db.scalar(select(IntegrationEvent).where(IntegrationEvent.id == event.id))
        if failed is not None:
            failed.status = "failed"; failed.attempts = (failed.attempts or 0) + 1; failed.last_error = str(exc)[:4000]; failed.next_attempt_at = datetime.now(timezone.utc) + timedelta(seconds=min(300, 2 ** min(failed.attempts, 8))); db.commit()
        return {"error": str(exc)}

def _rows(db: Session, model, company_id: int, limit: int): return db.scalars(select(model).where(model.company_id == company_id).order_by(model.id.desc()).limit(limit)).all()
def _json_rows(rows): return [{c.name: getattr(row, c.name) for c in row.__table__.columns} for row in rows]

@router.post("/connections", response_model=ConnectionResponse, status_code=201, dependencies=[Depends(require_permission("integrations.write"))])
def create_connection(payload: ConnectionCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, payload.company_id, current_user)
    if payload.provider.lower() not in {"salla", "generic"}: raise HTTPException(400, "Unsupported provider")
    obj = IntegrationConnection(**payload.model_dump(), provider=payload.provider.lower()); db.add(obj)
    try: db.commit(); db.refresh(obj)
    except IntegrityError as exc: db.rollback(); raise HTTPException(409, "Integration connection already exists") from exc
    return obj

@router.get("/connections", response_model=list[ConnectionResponse])
def list_connections(company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user); return db.scalars(select(IntegrationConnection).where(IntegrationConnection.company_id == company_id).order_by(IntegrationConnection.id.desc())).all()

@router.post("/salla/{connection_id}/sync", status_code=202, dependencies=[Depends(require_permission("integrations.write"))])
def sync_salla(connection_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    connection = _get_salla_connection(db, connection_id)
    _company_for_user(db, connection.company_id, current_user)
    return full_sync(db, connection)

@public_router.post("/salla/{connection_id}/webhook")
async def salla_webhook(connection_id: int, request: Request, x_salla_signature: str | None = Header(default=None), x_salla_event: str | None = Header(default=None), x_salla_event_id: str | None = Header(default=None), signature_strategy: str | None = Query(default=None), db: Session = Depends(get_db)):
    connection = _get_salla_connection(db, connection_id)
    raw_body = await request.body()
    if len(raw_body) > MAX_WEBHOOK_BODY_BYTES: raise HTTPException(413, "Webhook body exceeds the configured size limit")
    _verify_salla_signature(connection, raw_body, signature_strategy, x_salla_signature)
    try: payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc: raise HTTPException(400, "Webhook body must be valid UTF-8 JSON") from exc
    if not isinstance(payload, dict): raise HTTPException(422, "Webhook payload must be a JSON object")
    external_event_id, event_type = _event_identity(payload, x_salla_event, x_salla_event_id, raw_body)
    event = db.scalar(select(IntegrationEvent).where(IntegrationEvent.connection_id == connection_id, IntegrationEvent.external_event_id == external_event_id))
    if event is None:
        event = IntegrationEvent(connection_id=connection_id, company_id=connection.company_id, external_event_id=external_event_id, event_type=event_type, payload=payload, status="received", attempts=0)
        db.add(event)
        try: db.commit(); db.refresh(event)
        except IntegrityError: db.rollback(); event = db.scalar(select(IntegrationEvent).where(IntegrationEvent.connection_id == connection_id, IntegrationEvent.external_event_id == external_event_id))
    result = _process_event(db, event)
    return {"accepted": True, "event_id": event.id, "status": event.status, "result": result}
