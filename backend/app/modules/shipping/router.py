from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from .models import ShippingProvider, ShippingPaymentProfile, Shipment, ShipmentEvent
from .schemas import ProviderCreate, ProviderRead, PaymentProfileCreate, PaymentProfileRead, ShipmentCreate, ShipmentRead, ShipmentStatusUpdate
from .templates import PROVIDER_TEMPLATES

router = APIRouter(prefix="/shipping", tags=["Shipping & Logistics"])


def _tenant_provider(db: Session, tenant_id: int, provider_id: int) -> ShippingProvider:
    item = db.query(ShippingProvider).filter(ShippingProvider.id == provider_id, ShippingProvider.tenant_id == tenant_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Shipping provider not found for tenant")
    return item


@router.get("/provider-templates")
def provider_templates():
    return {"success": True, "data": PROVIDER_TEMPLATES, "warning": "Payment, COD and settlement terms are templates only; apply the customer's current contract/tariff."}


@router.get("/providers", response_model=list[ProviderRead])
def list_providers(tenant_id: int = Query(..., ge=1), db: Session = Depends(get_db)):
    return db.query(ShippingProvider).filter(ShippingProvider.tenant_id == tenant_id, ShippingProvider.active.is_(True)).order_by(ShippingProvider.name).all()


@router.post("/providers", response_model=ProviderRead, status_code=201)
def create_provider(payload: ProviderCreate, db: Session = Depends(get_db)):
    if db.query(ShippingProvider).filter(ShippingProvider.tenant_id == payload.tenant_id, ShippingProvider.code == payload.code).first():
        raise HTTPException(status_code=409, detail="Provider code already exists for this tenant")
    item = ShippingProvider(**payload.model_dump())
    db.add(item); db.commit(); db.refresh(item)
    return item


@router.get("/providers/{provider_id}/payment-profiles", response_model=list[PaymentProfileRead])
def list_payment_profiles(provider_id: int, tenant_id: int = Query(..., ge=1), db: Session = Depends(get_db)):
    _tenant_provider(db, tenant_id, provider_id)
    return db.query(ShippingPaymentProfile).filter(ShippingPaymentProfile.provider_id == provider_id, ShippingPaymentProfile.active.is_(True)).all()


@router.post("/providers/{provider_id}/payment-profiles", response_model=PaymentProfileRead, status_code=201)
def create_payment_profile(provider_id: int, payload: PaymentProfileCreate, tenant_id: int = Query(..., ge=1), db: Session = Depends(get_db)):
    if payload.provider_id != provider_id: raise HTTPException(status_code=400, detail="provider_id mismatch")
    _tenant_provider(db, tenant_id, provider_id)
    item = ShippingPaymentProfile(**payload.model_dump())
    db.add(item); db.commit(); db.refresh(item)
    return item


@router.post("/shipments", response_model=ShipmentRead, status_code=201)
def create_shipment(payload: ShipmentCreate, db: Session = Depends(get_db)):
    _tenant_provider(db, payload.tenant_id, payload.provider_id)
    if payload.payment_method == "cod" and payload.cod_amount <= 0:
        raise HTTPException(status_code=422, detail="COD shipment must have a positive cod_amount")
    item = Shipment(**payload.model_dump())
    db.add(item); db.flush()
    db.add(ShipmentEvent(shipment_id=item.id, status="draft", event_code="CREATED", description="Shipment created"))
    db.commit(); db.refresh(item)
    return item


@router.get("/shipments", response_model=list[ShipmentRead])
def list_shipments(tenant_id: int = Query(..., ge=1), status: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Shipment).filter(Shipment.tenant_id == tenant_id)
    if status: q = q.filter(Shipment.status == status)
    return q.order_by(Shipment.id.desc()).limit(500).all()


@router.get("/shipments/{shipment_id}", response_model=ShipmentRead)
def get_shipment(shipment_id: int, tenant_id: int = Query(..., ge=1), db: Session = Depends(get_db)):
    item = db.query(Shipment).filter(Shipment.id == shipment_id, Shipment.tenant_id == tenant_id).first()
    if not item: raise HTTPException(status_code=404, detail="Shipment not found")
    return item


@router.post("/shipments/{shipment_id}/status", response_model=ShipmentRead)
def update_shipment_status(shipment_id: int, payload: ShipmentStatusUpdate, tenant_id: int = Query(..., ge=1), db: Session = Depends(get_db)):
    item = db.query(Shipment).filter(Shipment.id == shipment_id, Shipment.tenant_id == tenant_id).first()
    if not item: raise HTTPException(status_code=404, detail="Shipment not found")
    now = datetime.now(timezone.utc)
    item.status = payload.status
    if payload.tracking_number: item.tracking_number = payload.tracking_number
    if payload.status == "shipped": item.shipped_at = now
    elif payload.status == "delivered": item.delivered_at = now
    elif payload.status == "returned": item.returned_at = now
    db.add(ShipmentEvent(shipment_id=item.id, status=payload.status, event_code=payload.event_code, description=payload.description))
    db.commit(); db.refresh(item)
    return item
