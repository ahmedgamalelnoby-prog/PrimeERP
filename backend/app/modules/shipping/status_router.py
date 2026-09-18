import json
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.saas.entitlements import require_module
from app.modules.shipping.models import Shipment
from app.modules.shipping.status_models import ShippingFinancialEvent, ShippingOrderStatus
from app.modules.shipping.status_schemas import ShippingStatusCreate
from app.modules.shipping.status_service import shipping_status_service

ALLOWED_FINANCIAL_ACTIONS = {
    "recognize_revenue", "recognize_shipping_revenue", "recognize_shipping_cost", "create_cod_receivable",
    "recognize_cod_fee", "recognize_card_fee", "reverse_revenue", "reverse_shipping_revenue",
    "reverse_cod_receivable", "recognize_return_cost",
}

router = APIRouter(
    prefix="/shipping/order-statuses",
    tags=["Shipping Order Statuses"],
    dependencies=[Depends(require_permission("shipping.access")), Depends(require_module("shipping"))],
)


def _company(db: Session, company_id: int, user: User):
    if user.tenant_id is None:
        raise HTTPException(403, "User is not assigned to a tenant")
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == user.tenant_id, Company.is_active.is_(True)))
    if company is None:
        raise HTTPException(403, "Company is outside the current tenant or inactive")
    return company


def _dump(status: ShippingOrderStatus):
    return {
        "id": status.id, "company_id": status.company_id, "code": status.code,
        "name": status.name, "name_ar": status.name_ar, "parent_code": status.parent_code,
        "sort_order": status.sort_order, "is_active": status.is_active,
        "financial_actions": json.loads(status.financial_actions or "[]"),
        "allowed_next_codes": json.loads(status.allowed_next_codes or "[]"),
    }


@router.get("")
def list_statuses(company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, company_id, current_user)
    shipping_status_service.ensure_defaults(db, company_id)
    return [_dump(x) for x in db.scalars(select(ShippingOrderStatus).where(ShippingOrderStatus.company_id == company_id).order_by(ShippingOrderStatus.sort_order, ShippingOrderStatus.id)).all()]


@router.post("", status_code=201, dependencies=[Depends(require_permission("shipping.write"))])
def create_status(payload: ShippingStatusCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, payload.company_id, current_user)
    unknown_actions = set(payload.financial_actions) - ALLOWED_FINANCIAL_ACTIONS
    if unknown_actions:
        raise HTTPException(422, f"Unsupported financial actions: {sorted(unknown_actions)}")
    if payload.code in payload.allowed_next_codes:
        raise HTTPException(422, "A status cannot transition to itself")
    if payload.allowed_next_codes:
        known = set(db.scalars(select(ShippingOrderStatus.code).where(ShippingOrderStatus.company_id == payload.company_id)).all()) | {payload.code}
        unknown_next = set(payload.allowed_next_codes) - known
        if unknown_next:
            raise HTTPException(422, f"Unknown next statuses: {sorted(unknown_next)}")
    if db.scalar(select(ShippingOrderStatus.id).where(ShippingOrderStatus.company_id == payload.company_id, ShippingOrderStatus.code == payload.code)):
        raise HTTPException(409, "Status code already exists")
    obj = ShippingOrderStatus(**payload.model_dump(exclude={"financial_actions", "allowed_next_codes", "company_id"}), company_id=payload.company_id, financial_actions=json.dumps(payload.financial_actions), allowed_next_codes=json.dumps(payload.allowed_next_codes))
    db.add(obj); db.commit(); db.refresh(obj)
    return _dump(obj)


@router.put("/{status_id}", dependencies=[Depends(require_permission("shipping.write"))])
def update_status(status_id: int, payload: ShippingStatusCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, payload.company_id, current_user)
    unknown_actions = set(payload.financial_actions) - ALLOWED_FINANCIAL_ACTIONS
    if unknown_actions:
        raise HTTPException(422, f"Unsupported financial actions: {sorted(unknown_actions)}")
    if payload.code in payload.allowed_next_codes:
        raise HTTPException(422, "A status cannot transition to itself")
    if payload.allowed_next_codes:
        known = set(db.scalars(select(ShippingOrderStatus.code).where(
            ShippingOrderStatus.company_id == payload.company_id
        )).all())
        unknown_next = set(payload.allowed_next_codes) - known
        if unknown_next:
            raise HTTPException(422, f"Unknown next statuses: {sorted(unknown_next)}")
    if payload.parent_code and payload.parent_code == payload.code:
        raise HTTPException(422, "A status cannot be its own parent")
    obj = db.scalar(select(ShippingOrderStatus).where(ShippingOrderStatus.id == status_id, ShippingOrderStatus.company_id == payload.company_id))
    if obj is None:
        raise HTTPException(404, "Shipping status not found")
    duplicate = db.scalar(select(ShippingOrderStatus.id).where(ShippingOrderStatus.company_id == payload.company_id, ShippingOrderStatus.code == payload.code, ShippingOrderStatus.id != status_id))
    if duplicate:
        raise HTTPException(409, "Status code already exists")
    for key in ("code", "name", "name_ar", "parent_code", "sort_order", "is_active"):
        setattr(obj, key, getattr(payload, key))
    obj.financial_actions = json.dumps(payload.financial_actions)
    obj.allowed_next_codes = json.dumps(payload.allowed_next_codes)
    db.commit(); db.refresh(obj)
    return _dump(obj)


@router.get("/financial-events")
def financial_events(company_id: int = Query(..., gt=0), carrier_id: int | None = Query(default=None, gt=0), shipment_id: int | None = Query(default=None, gt=0), date_from: date | None = None, date_to: date | None = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, company_id, current_user)
    stmt = select(ShippingFinancialEvent).where(ShippingFinancialEvent.company_id == company_id)
    if carrier_id: stmt = stmt.where(ShippingFinancialEvent.carrier_id == carrier_id)
    if shipment_id: stmt = stmt.where(ShippingFinancialEvent.shipment_id == shipment_id)
    if date_from: stmt = stmt.where(ShippingFinancialEvent.event_date >= date_from)
    if date_to: stmt = stmt.where(ShippingFinancialEvent.event_date <= date_to)
    return list(db.scalars(stmt.order_by(ShippingFinancialEvent.event_date.desc(), ShippingFinancialEvent.id.desc())).all())


@router.get("/{company_id}/defaults", include_in_schema=False)
def ensure_default_statuses(company_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, company_id, current_user)
    shipping_status_service.ensure_defaults(db, company_id)
    db.commit()
    return {"company_id": company_id, "status": "ready"}
