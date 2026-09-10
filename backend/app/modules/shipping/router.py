from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from .models import ShippingProvider, ShippingPaymentProfile, Shipment, ShipmentEvent
from .connection_models import ShippingConnection
from .schemas import ProviderCreate, ProviderRead, PaymentProfileCreate, PaymentProfileRead, ShipmentCreate, ShipmentRead, ShipmentStatusUpdate
from .templates import PROVIDER_TEMPLATES
from .connectors.registry import manifest_for

router = APIRouter(prefix="/shipping", tags=["Shipping & Logistics"])


def require_tenant_user(current_user: User) -> int:
    if current_user.is_platform_admin or current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Active tenant context is required")
    return current_user.tenant_id


def _tenant_provider(db: Session, tenant_id: int, provider_id: int) -> ShippingProvider:
    item = db.query(ShippingProvider).filter(ShippingProvider.id == provider_id, ShippingProvider.tenant_id == tenant_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Shipping provider not found for tenant")
    return item


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
    if payload.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access to another tenant is not allowed")
    if db.query(ShippingProvider).filter(ShippingProvider.tenant_id == tenant_id, ShippingProvider.code == payload.code).first():
        raise HTTPException(status_code=409, detail="Provider code already exists for this tenant")
    item = ShippingProvider(**payload.model_dump())
    db.add(item); db.commit(); db.refresh(item)
    return item


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
    if payload.get("tenant_id") not in (None, tenant_id): raise HTTPException(status_code=403, detail="Access to another tenant is not allowed")
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
    tenant_id = require_tenant_user(current_user)
    row = db.query(ShippingConnection, ShippingProvider.code).join(ShippingProvider, ShippingProvider.id == ShippingConnection.provider_id).filter(ShippingConnection.id == connection_id, ShippingConnection.tenant_id == tenant_id).first()
    if not row: raise HTTPException(status_code=404, detail="Shipping connection not found")
    connection, code = row
    manifest = manifest_for(code)
    return {"success": True, "connection_id": connection.id, "provider": code, "manifest": manifest.__dict__, "configured": bool(connection.secret_ref or connection.account_reference), "message": "Connector configuration is present; provider credentials are resolved at runtime from secret references."}


@router.post("/shipments", response_model=ShipmentRead, status_code=201)
def create_shipment(payload: ShipmentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tenant_id = require_tenant_user(current_user)
    if payload.tenant_id != tenant_id: raise HTTPException(status_code=403, detail="Access to another tenant is not allowed")
    _tenant_provider(db, tenant_id, payload.provider_id)
    if payload.payment_method == "cod" and payload.cod_amount <= 0: raise HTTPException(status_code=422, detail="COD shipment must have a positive cod_amount")
    item = Shipment(**payload.model_dump()); db.add(item); db.flush(); db.add(ShipmentEvent(shipment_id=item.id, status="draft", event_code="CREATED", description="Shipment created")); db.commit(); db.refresh(item); return item


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
