from datetime import datetime, timezone
import os
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from .models import ShippingProvider, ShippingPaymentProfile, Shipment, ShipmentEvent
from .connection_models import ShippingConnection
from .schemas import ProviderCreate, ProviderRead, PaymentProfileCreate, PaymentProfileRead, ShipmentCreate, ShipmentRead, ShipmentStatusUpdate, ShipmentExecuteRequest, ShipmentExecuteResponse, ShipmentTrackResponse
from .templates import PROVIDER_TEMPLATES
from .connectors.registry import manifest_for
from .services.integration_service import connector_for, create_shipping_transaction, normalize_provider_result

router = APIRouter(prefix="/shipping", tags=["Shipping & Logistics"])

def require_tenant_user(current_user: User) -> int:
    if current_user.is_platform_admin or current_user.tenant_id is None:
        raise HTTPException(status_code=403, detail="Active tenant context is required")
    return current_user.tenant_id

def _tenant_provider(db: Session, tenant_id: int, provider_id: int) -> ShippingProvider:
    item = db.query(ShippingProvider).filter(ShippingProvider.id == provider_id, ShippingProvider.tenant_id == tenant_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Shipping provider not found for tenant")
    return item

def _tenant_connection(db: Session, tenant_id: int, connection_id: int):
    row = db.query(ShippingConnection, ShippingProvider).join(ShippingProvider, ShippingProvider.id == ShippingConnection.provider_id).filter(ShippingConnection.id == connection_id, ShippingConnection.tenant_id == tenant_id, ShippingConnection.enabled.is_(True)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Shipping connection not found or disabled")
    return row[0], row[1]

@router.get("/provider-templates")
def provider_templates():
    return {"success": True, "data": PROVIDER_TEMPLATES, "warning": "Payment, COD and settlement terms are templates only; apply the customer's current contract/tariff."}

@router.get("/connector-manifests")
def connector_manifests():
    return {"success": True, "data": [manifest_for(t["code"]).__dict__ for t in PROVIDER_TEMPLATES]}

@router.get("/providers", response_model=list[ProviderRead])
def list_providers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tenant_id = require_tenant_user(current_user)
    return db.query(ShippingProvider).filter(ShippingProvider.tenant_id == tenant_id, ShippingProvider.active.is_(True)).order_by(ShippingProvider.name).all()

@router.post("/providers", response_model=ProviderRead, status_code=201)
def create_provider(payload: ProviderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tenant_id = require_tenant_user(current_user)
    if payload.tenant_id != tenant_id: raise HTTPException(status_code=403, detail="Access to another tenant is not allowed")
    if db.query(ShippingProvider).filter(ShippingProvider.tenant_id == tenant_id, ShippingProvider.code == payload.code).first(): raise HTTPException(status_code=409, detail="Provider code already exists for this tenant")
    item = ShippingProvider(**payload.model_dump()); db.add(item); db.commit(); db.refresh(item); return item

@router.get("/providers/{provider_id}/payment-profiles", response_model=list[PaymentProfileRead])
def list_payment_profiles(provider_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tenant_id = require_tenant_user(current_user); _tenant_provider(db, tenant_id, provider_id)
    return db.query(ShippingPaymentProfile).filter(ShippingPaymentProfile.provider_id == provider_id, ShippingPaymentProfile.active.is_(True)).all()

@router.post("/providers/{provider_id}/payment-profiles", response_model=PaymentProfileRead, status_code=201)
def create_payment_profile(provider_id: int, payload: PaymentProfileCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tenant_id = require_tenant_user(current_user)
    if payload.provider_id != provider_id: raise HTTPException(status_code=400, detail="provider_id mismatch")
    _tenant_provider(db, tenant_id, provider_id)
    item = ShippingPaymentProfile(**payload.model_dump()); db.add(item); db.commit(); db.refresh(item); return item

@router.post("/connections", status_code=201)
def create_connection(payload: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tenant_id = require_tenant_user(current_user)
    provider = _tenant_provider(db, tenant_id, int(payload["provider_id"]))
    item = ShippingConnection(tenant_id=tenant_id, provider_id=provider.id, name=payload["name"], environment=payload.get("environment", "production"), base_url=payload.get("base_url"), auth_type=payload.get("auth_type", "api_key"), secret_ref=payload.get("secret_ref"), account_reference=payload.get("account_reference"), webhook_secret_ref=payload.get("webhook_secret_ref"), notes=payload.get("notes"))
    db.add(item); db.commit(); db.refresh(item)
    return {"id": item.id, "provider_id": item.provider_id, "name": item.name, "environment": item.environment, "base_url": item.base_url, "auth_type": item.auth_type, "account_reference": item.account_reference, "enabled": item.enabled, "manifest": manifest_for(provider.code).__dict__}

@router.get("/connections")
def list_connections(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tenant_id = require_tenant_user(current_user)
    rows = db.query(ShippingConnection, ShippingProvider.code, ShippingProvider.name).join(ShippingProvider, ShippingProvider.id == ShippingConnection.provider_id).filter(ShippingConnection.tenant_id == tenant_id).order_by(ShippingConnection.id.desc()).all()
    return [{"id": r.ShippingConnection.id, "provider_id": r.ShippingConnection.provider_id, "provider_code": r.code, "provider_name": r.name, "name": r.ShippingConnection.name, "environment": r.ShippingConnection.environment, "base_url": r.ShippingConnection.base_url, "auth_type": r.ShippingConnection.auth_type, "account_reference": r.ShippingConnection.account_reference, "enabled": r.ShippingConnection.enabled, "manifest": manifest_for(r.code).__dict__} for r in rows]

@router.get("/connections/{connection_id}/health")
def connection_health(connection_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tenant_id = require_tenant_user(current_user); connection, provider = _tenant_connection(db, tenant_id, connection_id)
    return {"success": True, "connection_id": connection.id, "provider": provider.code, "manifest": manifest_for(provider.code).__dict__, "configured": bool(connection.secret_ref or connection.account_reference), "message": "Connector configuration is present; provider credentials are resolved at runtime from secret references."}

@router.post("/shipments", response_model=ShipmentRead, status_code=201)
def create_shipment(payload: ShipmentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tenant_id = require_tenant_user(current_user)
    if payload.tenant_id != tenant_id: raise HTTPException(status_code=403, detail="Access to another tenant is not allowed")
    _tenant_provider(db, tenant_id, payload.provider_id)
    if payload.payment_method == "cod" and payload.cod_amount <= 0: raise HTTPException(status_code=422, detail="COD shipment must have a positive cod_amount")
    item = Shipment(**payload.model_dump()); db.add(item); db.flush(); db.add(ShipmentEvent(shipment_id=item.id, status="draft", event_code="CREATED", description="Shipment created")); db.commit(); db.refresh(item)
    if item.company_id and item.branch_id:
        transaction = create_shipping_transaction(db, item, current_user)
        item.transaction_id = transaction.id
        db.commit(); db.refresh(item)
    return item

@router.get("/shipments", response_model=list[ShipmentRead])
def list_shipments(status_filter: str | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tenant_id = require_tenant_user(current_user); q = db.query(Shipment).filter(Shipment.tenant_id == tenant_id)
    if status_filter: q = q.filter(Shipment.status == status_filter)
    return q.order_by(Shipment.id.desc()).limit(500).all()

@router.get("/shipments/{shipment_id}", response_model=ShipmentRead)
def get_shipment(shipment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tenant_id = require_tenant_user(current_user); item = db.query(Shipment).filter(Shipment.id == shipment_id, Shipment.tenant_id == tenant_id).first()
    if not item: raise HTTPException(status_code=404, detail="Shipment not found")
    return item

@router.post("/shipments/{shipment_id}/execute", response_model=ShipmentExecuteResponse)
def execute_shipment(shipment_id: int, payload: ShipmentExecuteRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tenant_id = require_tenant_user(current_user)
    item = db.query(Shipment).filter(Shipment.id == shipment_id, Shipment.tenant_id == tenant_id).first()
    if not item: raise HTTPException(status_code=404, detail="Shipment not found")
    connection, provider = _tenant_connection(db, tenant_id, payload.connection_id)
    if connection.provider_id != item.provider_id: raise HTTPException(status_code=400, detail="Connection provider does not match shipment provider")
    connector = connector_for(connection, provider)
    provider_code = provider.code.upper()
    if payload.provider_payload is not None:
        request_payload = payload.provider_payload
    elif provider_code == "BOSTA":
        request_payload = {"type": 10, "cod": float(item.cod_amount or 0), "businessReference": item.reference, "receiver": {"firstName": item.customer_name, "phone": item.customer_phone or ""}, "dropOffAddress": {"firstLine": item.address or "", "city": item.city or ""}}
    else:
        request_payload = {"reference": item.reference, "tracking_number": item.tracking_number, "customer_name": item.customer_name, "customer_phone": item.customer_phone, "address": item.address, "city": item.city, "cod_amount": float(item.cod_amount or 0), "weight_kg": float(item.weight_kg or item.volumetric_weight_kg or 0)}
    try:
        result = connector.create_delivery(request_payload) if provider_code == "BOSTA" else connector.create_shipment(request_payload)
        normalized = normalize_provider_result(provider_code, result)
    except Exception as exc:
        item.status = "integration_failed"
        db.add(ShipmentEvent(shipment_id=item.id, status="integration_failed", event_code="PROVIDER_ERROR", description=str(exc)[:1000]))
        db.commit()
        raise HTTPException(status_code=502, detail=f"Shipping provider request failed: {exc}") from exc
    item.external_id = normalized["external_id"] or item.external_id
    item.tracking_number = normalized["tracking_number"] or item.tracking_number
    item.status = "submitted"
    db.add(ShipmentEvent(shipment_id=item.id, status="submitted", event_code="PROVIDER_CREATED", description="Shipment submitted to provider"))
    db.commit(); db.refresh(item)
    return ShipmentExecuteResponse(shipment_id=item.id, provider=provider_code, status=item.status, tracking_number=item.tracking_number, external_id=item.external_id, raw=normalized["raw"])

@router.post("/shipments/{shipment_id}/track", response_model=ShipmentTrackResponse)
def track_shipment(shipment_id: int, connection_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tenant_id = require_tenant_user(current_user)
    item = db.query(Shipment).filter(Shipment.id == shipment_id, Shipment.tenant_id == tenant_id).first()
    if not item: raise HTTPException(status_code=404, detail="Shipment not found")
    if not item.tracking_number: raise HTTPException(status_code=422, detail="Shipment has no tracking number")
    connection, provider = _tenant_connection(db, tenant_id, connection_id)
    if connection.provider_id != item.provider_id: raise HTTPException(status_code=400, detail="Connection provider does not match shipment provider")
    connector = connector_for(connection, provider)
    try:
        result = connector.track(item.tracking_number)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Tracking request failed: {exc}") from exc
    db.add(ShipmentEvent(shipment_id=item.id, status=item.status, event_code="TRACKED", description="Tracking synchronized", raw_payload=str(result)))
    db.commit()
    return ShipmentTrackResponse(shipment_id=item.id, provider=provider.code, tracking_number=item.tracking_number, raw=result)

@router.post("/shipments/{shipment_id}/status", response_model=ShipmentRead)
def update_shipment_status(shipment_id: int, payload: ShipmentStatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tenant_id = require_tenant_user(current_user); item = db.query(Shipment).filter(Shipment.id == shipment_id, Shipment.tenant_id == tenant_id).first()
    if not item: raise HTTPException(status_code=404, detail="Shipment not found")
    now = datetime.now(timezone.utc); item.status = payload.status
    if payload.tracking_number: item.tracking_number = payload.tracking_number
    if payload.status == "shipped": item.shipped_at = now
    elif payload.status == "delivered": item.delivered_at = now
    elif payload.status == "returned": item.returned_at = now
    db.add(ShipmentEvent(shipment_id=item.id, status=payload.status, event_code=payload.event_code, description=payload.description)); db.commit(); db.refresh(item); return item

@router.post("/webhooks/{provider_code}/{connection_id}")
def provider_webhook(provider_code: str, connection_id: int, payload: dict, x_webhook_secret: str | None = Header(default=None), db: Session = Depends(get_db)):
    row = db.query(ShippingConnection, ShippingProvider).join(ShippingProvider, ShippingProvider.id == ShippingConnection.provider_id).filter(ShippingConnection.id == connection_id, ShippingProvider.code == provider_code.upper(), ShippingConnection.enabled.is_(True)).first()
    if not row: raise HTTPException(status_code=404, detail="Webhook connection not found")
    connection, provider = row
    if connection.webhook_secret_ref:
        expected = os.getenv(connection.webhook_secret_ref)
        if not expected or x_webhook_secret != expected: raise HTTPException(status_code=401, detail="Invalid webhook secret")
    tracking = payload.get("trackingNumber") or payload.get("tracking_number")
    reference = payload.get("businessReference") or payload.get("reference")
    if not tracking and not reference: raise HTTPException(status_code=422, detail="Webhook must contain trackingNumber or businessReference")
    q = db.query(Shipment).filter(Shipment.tenant_id == connection.tenant_id, Shipment.provider_id == provider.id)
    item = q.filter(Shipment.tracking_number == str(tracking)).first() if tracking else None
    if not item and reference: item = q.filter(Shipment.reference == str(reference)).first()
    if not item: return {"accepted": True, "matched": False}
    state = payload.get("state")
    status_map = {"delivered": "delivered", "out_for_delivery": "out_for_delivery", "exception": "exception", "returned": "returned", "terminated": "cancelled"}
    normalized_status = status_map.get(str(state).lower(), item.status)
    item.status = normalized_status
    now = datetime.now(timezone.utc)
    if normalized_status == "delivered": item.delivered_at = now
    elif normalized_status == "returned": item.returned_at = now
    if tracking: item.tracking_number = str(tracking)
    db.add(ShipmentEvent(shipment_id=item.id, status=normalized_status, event_code=str(state) if state is not None else None, description="Provider webhook", raw_payload=str(payload)))
    db.commit()
    return {"accepted": True, "matched": True, "shipment_id": item.id, "status": item.status}
