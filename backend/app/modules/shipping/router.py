from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.accounting.chart_of_accounts.models import AccountCombination
from app.modules.shipping.models import ShippingCarrier, ShippingMethod, Shipment
from app.modules.shipping.schemas import CarrierCreate, CarrierResponse, MethodCreate, MethodResponse, ShipmentCreate, ShipmentResponse
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User

router = APIRouter(
    prefix="/shipping",
    tags=["Shipping"],
    dependencies=[Depends(require_permission("shipping.access"))],
)


def _company_for_user(db: Session, company_id: int, user: User):
    if user.tenant_id is None:
        raise HTTPException(403, "User is not assigned to a tenant")
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == user.tenant_id))
    if company is None:
        raise HTTPException(403, "Company is outside the current tenant")
    return company


def _validate_payment_account(db: Session, company_id: int, account_id: int | None):
    if account_id is None:
        return
    account = db.scalar(select(AccountCombination).where(
        AccountCombination.id == account_id,
        AccountCombination.company_id == company_id,
        AccountCombination.is_active.is_(True),
    ))
    if account is None:
        raise HTTPException(422, "Shipping payment account does not belong to the company or is inactive")


@router.post("/carriers", response_model=CarrierResponse, status_code=201, dependencies=[Depends(require_permission("shipping.write"))])
def carrier(p: CarrierCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, p.company_id, current_user)
    if db.scalar(select(ShippingCarrier).where(ShippingCarrier.company_id == p.company_id, ShippingCarrier.code == p.code)):
        raise HTTPException(409, "Carrier code already exists")
    o = ShippingCarrier(**p.model_dump())
    db.add(o)
    db.commit()
    db.refresh(o)
    return o


@router.get("/carriers", response_model=list[CarrierResponse])
def carriers(company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    return list(db.scalars(select(ShippingCarrier).where(ShippingCarrier.company_id == company_id, ShippingCarrier.is_active.is_(True)).order_by(ShippingCarrier.name)).all())


@router.post("/methods", response_model=MethodResponse, status_code=201, dependencies=[Depends(require_permission("shipping.write"))])
def method(p: MethodCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    carrier = db.scalar(select(ShippingCarrier).join(Company, Company.id == ShippingCarrier.company_id).where(ShippingCarrier.id == p.carrier_id, Company.tenant_id == current_user.tenant_id, ShippingCarrier.is_active.is_(True)))
    if carrier is None:
        raise HTTPException(404, "Carrier not found")
    if p.payment_method not in {"prepaid", "cod", "mixed"}:
        raise HTTPException(422, "Invalid shipping payment method")
    if p.payment_method == "prepaid" and p.cod_fee_percent:
        raise HTTPException(422, "COD fee is not valid for prepaid-only methods")
    _validate_payment_account(db, carrier.company_id, p.payment_account_id)
    o = ShippingMethod(carrier_id=carrier.id, **p.model_dump(exclude={"carrier_id"}))
    db.add(o)
    db.commit()
    db.refresh(o)
    return o


@router.get("/methods", response_model=list[MethodResponse])
def methods(carrier_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    carrier = db.scalar(select(ShippingCarrier).join(Company, Company.id == ShippingCarrier.company_id).where(ShippingCarrier.id == carrier_id, Company.tenant_id == current_user.tenant_id))
    if carrier is None:
        raise HTTPException(404, "Carrier not found")
    return list(db.scalars(select(ShippingMethod).where(ShippingMethod.carrier_id == carrier_id)).all())


@router.post("/shipments", response_model=ShipmentResponse, status_code=201, dependencies=[Depends(require_permission("shipping.write"))])
def shipment(p: ShipmentCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, p.company_id, current_user)
    m = db.scalar(select(ShippingMethod).join(ShippingCarrier, ShippingCarrier.id == ShippingMethod.carrier_id).where(ShippingMethod.id == p.method_id, ShippingMethod.carrier_id == p.carrier_id, ShippingCarrier.company_id == p.company_id, ShippingCarrier.is_active.is_(True)))
    if not m:
        raise HTTPException(400, "Invalid carrier/method for company")
    if p.cod_amount and m.payment_method == "prepaid":
        raise HTTPException(422, "COD amount is not allowed for prepaid shipping")
    fee = p.shipping_fee if p.shipping_fee > 0 else m.base_fee
    if m.payment_method in {"cod", "mixed"} and p.cod_amount:
        fee += p.cod_amount * m.cod_fee_percent / 100
    o = Shipment(**p.model_dump(), shipping_fee=fee)
    db.add(o)
    db.commit()
    db.refresh(o)
    return o


@router.get("/shipments", response_model=list[ShipmentResponse])
def shipments(company_id: int = Query(..., gt=0), status: str | None = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    q = select(Shipment).where(Shipment.company_id == company_id)
    if status:
        q = q.where(Shipment.status == status)
    return list(db.scalars(q.order_by(Shipment.id.desc())).all())


_TRANSITIONS = {
    "pending": {"picked_up", "cancelled"},
    "picked_up": {"in_transit", "cancelled"},
    "in_transit": {"out_for_delivery", "returned"},
    "out_for_delivery": {"delivered", "returned"},
    "delivered": {"returned"},
    "returned": set(),
    "cancelled": set(),
}


@router.post("/shipments/{shipment_id}/status", response_model=ShipmentResponse, dependencies=[Depends(require_permission("shipping.post"))])
def status(shipment_id: int, value: str = Query(...), company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    o = db.scalar(select(Shipment).where(Shipment.id == shipment_id, Shipment.company_id == company_id).with_for_update())
    if not o:
        raise HTTPException(404, "Shipment not found")
    if value not in _TRANSITIONS:
        raise HTTPException(400, "Invalid shipment status")
    if value == o.status:
        return o
    if value not in _TRANSITIONS[o.status]:
        raise HTTPException(409, f"Invalid shipment transition: {o.status} -> {value}")
    o.status = value
    db.commit()
    db.refresh(o)
    return o
