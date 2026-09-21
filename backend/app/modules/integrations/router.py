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
from .salla_sync import full_sync, sync_salla_shipping_companies
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
        elif event_key.startswith("shipping.company") or event_key.startswith("shipping_company"):
            result["erp_shipping_companies"] = sync_salla_shipping_companies(db, event.connection_id)
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
def sync_salla(connection_id: int, from_date: str | None = Query(default=None), to_date: str | None = Query(default=None), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    connection = _get_salla_connection(db, connection_id); _company_for_user(db, connection.company_id, current_user)
    try: result = full_sync(db, connection_id, from_date=from_date, to_date=to_date)
    except Exception as exc: db.rollback(); raise HTTPException(502, f"Salla synchronization failed: {exc}") from exc
    return {"accepted": True, "connection_id": connection_id, "result": result}

@router.post("/salla/{connection_id}/execute", status_code=200, dependencies=[Depends(require_permission("integrations.write"))])
def execute_salla(connection_id: int, limit: int = Query(50, ge=1, le=500), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    connection = _get_salla_connection(db, connection_id); _company_for_user(db, connection.company_id, current_user)
    orders = db.scalars(select(SallaOrder).where(SallaOrder.company_id == connection.company_id, SallaOrder.connection_id == connection.id, SallaOrder.erp_status.in_(["pending", "failed"])).order_by(SallaOrder.id).limit(limit)).all()
    processed = failed = 0
    for order in orders:
        try: finalize_salla_order(db, order, user_id=current_user.id); db.commit(); processed += 1
        except Exception as exc:
            db.rollback(); failed += 1
            order = db.scalar(select(SallaOrder).where(SallaOrder.id == order.id, SallaOrder.company_id == connection.company_id))
            if order: order.erp_status = "failed"; order.erp_error = str(exc)[:4000]; db.commit()
    return {"connection_id": connection_id, "processed": processed, "failed": failed, "scanned": len(orders)}

@public_router.post("/salla/{connection_id}/webhook/public", status_code=202)
async def receive_salla_webhook_public(connection_id: int, request: Request, x_salla_security_strategy: str | None = Header(default=None, alias="X-Salla-Security-Strategy"), x_salla_signature: str | None = Header(default=None, alias="X-Salla-Signature"), x_salla_event: str | None = Header(default=None, alias="X-Salla-Event"), x_salla_event_id: str | None = Header(default=None, alias="X-Salla-Event-ID"), db: Session = Depends(get_db)):
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > MAX_WEBHOOK_BODY_BYTES: raise HTTPException(413, "Webhook payload is too large")
        except ValueError: raise HTTPException(400, "Invalid Content-Length header")
    connection = _get_salla_connection(db, connection_id); raw_body = await request.body()
    if len(raw_body) > MAX_WEBHOOK_BODY_BYTES: raise HTTPException(413, "Webhook payload is too large")
    _verify_salla_signature(connection, raw_body, x_salla_security_strategy, x_salla_signature)
    try: payload = json.loads(raw_body.decode())
    except (UnicodeDecodeError, json.JSONDecodeError) as exc: raise HTTPException(400, "Invalid webhook JSON") from exc
    if not isinstance(payload, dict): raise HTTPException(422, "Webhook payload must be a JSON object")
    external_event_id, event_type = _event_identity(payload, x_salla_event, x_salla_event_id, raw_body)
    existing = db.scalar(select(IntegrationEvent).where(IntegrationEvent.connection_id == connection_id, IntegrationEvent.external_event_id == external_event_id))
    if existing: return {"accepted": True, "duplicate": True, "event_id": existing.id, "status": existing.status}
    event = IntegrationEvent(company_id=connection.company_id, connection_id=connection_id, external_event_id=external_event_id, event_type=event_type, payload=json.dumps(payload, ensure_ascii=False), status="received", attempts=0); db.add(event); connection.last_sync_at = datetime.now(timezone.utc)
    try: db.commit(); db.refresh(event)
    except IntegrityError: db.rollback(); return {"accepted": True, "duplicate": True}
    result = _process_event(db, event)
    return {"accepted": True, "duplicate": False, "event_id": event.id, "status": "processed" if "error" not in result else "failed", "normalized": result}

@router.post("/salla/{connection_id}/webhook", status_code=202, dependencies=[Depends(require_permission("integrations.post"))])
def receive_salla_webhook(connection_id: int, payload: WebhookEventCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    connection = db.scalar(select(IntegrationConnection).join(Company, Company.id == IntegrationConnection.company_id).where(IntegrationConnection.id == connection_id, IntegrationConnection.provider == "salla", IntegrationConnection.is_active.is_(True), Company.tenant_id == current_user.tenant_id))
    if not connection: raise HTTPException(404, "Salla connection not found")
    existing = db.scalar(select(IntegrationEvent).where(IntegrationEvent.connection_id == connection_id, IntegrationEvent.external_event_id == payload.external_event_id))
    if existing: return {"accepted": True, "duplicate": True, "event_id": existing.id, "status": existing.status}
    event = IntegrationEvent(company_id=connection.company_id, connection_id=connection_id, external_event_id=payload.external_event_id, event_type=payload.event_type, payload=json.dumps(payload.payload, ensure_ascii=False), status="received", attempts=0); db.add(event); connection.last_sync_at = datetime.now(timezone.utc)
    try: db.commit(); db.refresh(event)
    except IntegrityError: db.rollback(); return {"accepted": True, "duplicate": True}
    result = _process_event(db, event)
    return {"accepted": True, "duplicate": False, "event_id": event.id, "status": "processed" if "error" not in result else "failed", "normalized": result}

@router.get("/salla/orders", status_code=200)
def list_salla_orders(company_id: int = Query(..., gt=0), limit: int = Query(100, ge=1, le=500), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user); return _json_rows(_rows(db, SallaOrder, company_id, limit))
@router.get("/salla/order-items", status_code=200)
def list_salla_order_items(company_id: int = Query(..., gt=0), limit: int = Query(200, ge=1, le=1000), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user); return _json_rows(_rows(db, SallaOrderItem, company_id, limit))
@router.get("/salla/customers", status_code=200)
def list_salla_customers(company_id: int = Query(..., gt=0), limit: int = Query(100, ge=1, le=500), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user); return _json_rows(_rows(db, SallaCustomer, company_id, limit))
@router.get("/salla/products", status_code=200)
def list_salla_products(company_id: int = Query(..., gt=0), limit: int = Query(100, ge=1, le=500), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user); return _json_rows(_rows(db, SallaProduct, company_id, limit))
@router.get("/salla/product-variants", status_code=200)
def list_salla_product_variants(company_id: int = Query(..., gt=0), limit: int = Query(200, ge=1, le=1000), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user); return _json_rows(_rows(db, SallaProductVariant, company_id, limit))
@router.get("/salla/shipments", status_code=200)
def list_salla_shipments(company_id: int = Query(..., gt=0), limit: int = Query(100, ge=1, le=500), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user); return _json_rows(_rows(db, SallaShipment, company_id, limit))
@router.get("/salla/invoices", status_code=200)
def list_salla_invoices(company_id: int = Query(..., gt=0), limit: int = Query(100, ge=1, le=500), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user); return _json_rows(_rows(db, SallaInvoice, company_id, limit))
@router.post("/events/{event_id}/replay", status_code=202, dependencies=[Depends(require_permission("integrations.write"))])
def replay_event(event_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    event = db.scalar(select(IntegrationEvent).join(Company, Company.id == IntegrationEvent.company_id).where(
        IntegrationEvent.id == event_id, Company.tenant_id == current_user.tenant_id
    ).with_for_update())
    if event is None:
        raise HTTPException(404, "Integration event not found")
    if event.status not in {"failed", "received"}:
        raise HTTPException(409, f"Only failed/received events can be replayed; current status is {event.status}")
    event.status = "received"
    event.next_attempt_at = None
    db.commit()
    result = _process_event(db, event)
    return {"event_id": event.id, "status": "processed" if "error" not in result else "failed", "result": result}

@router.get("/events", status_code=200)
def list_events(company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user); return db.scalars(select(IntegrationEvent).where(IntegrationEvent.company_id == company_id).order_by(IntegrationEvent.id.desc()).limit(200)).all()
@router.post("/events/{event_id}/retry", status_code=202, dependencies=[Depends(require_permission("integrations.post"))])
def retry_event(event_id: int, company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    event = db.scalar(select(IntegrationEvent).where(IntegrationEvent.id == event_id, IntegrationEvent.company_id == company_id).with_for_update())
    if event is None: raise HTTPException(404, "Integration event not found")
    if event.status == "processed": raise HTTPException(409, "Processed events cannot be retried")
    if event.attempts >= 10: event.status = "dead_letter"; db.commit(); raise HTTPException(409, "Maximum retry attempts reached; event moved to dead letter")
    event.attempts += 1; event.status = "queued"; event.next_attempt_at = datetime.now(timezone.utc) + timedelta(seconds=min(300, 2 ** min(event.attempts, 8))); event.last_error = None; db.commit()
    result = _process_event(db, event)
    return {"accepted": True, "event_id": event.id, "status": "processed" if "error" not in result else "failed", "attempts": event.attempts, "normalized": result}
