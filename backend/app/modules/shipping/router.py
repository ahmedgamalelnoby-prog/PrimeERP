from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.accounting.chart_of_accounts.models import AccountCombination
from app.modules.shipping.models import (
    ShippingCarrier, ShippingMethod, Shipment,
    ShippingSettlementBatch, ShippingShipmentSettlement,
)
from app.modules.shipping.schemas import (
    CarrierCreate, CarrierResponse, MethodCreate, MethodResponse,
    ShipmentCreate, ShipmentResponse, SettlementBatchCreate,
    SettlementBatchResponse, SettlementLineResponse,
)
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
    method = db.scalar(
        select(ShippingMethod)
        .join(ShippingCarrier, ShippingCarrier.id == ShippingMethod.carrier_id)
        .where(
            ShippingMethod.id == p.method_id,
            ShippingMethod.carrier_id == p.carrier_id,
            ShippingCarrier.company_id == p.company_id,
            ShippingCarrier.is_active.is_(True),
        )
    )
    if method is None:
        raise HTTPException(400, "Invalid carrier/method for company")
    if p.cod_amount and method.payment_method == "prepaid":
        raise HTTPException(422, "COD amount is not allowed for prepaid shipping")
    fee = p.shipping_fee if p.shipping_fee > 0 else method.base_fee
    if method.payment_method in {"cod", "mixed"} and p.cod_amount:
        fee += p.cod_amount * method.cod_fee_percent / 100
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


def _settlement_response(db: Session, batch: ShippingSettlementBatch) -> SettlementBatchResponse:
    lines = list(db.scalars(select(ShippingShipmentSettlement).where(ShippingShipmentSettlement.batch_id == batch.id).order_by(ShippingShipmentSettlement.id)).all())
    return SettlementBatchResponse(
        id=batch.id, company_id=batch.company_id, carrier_id=batch.carrier_id,
        reference=batch.reference, settlement_date=batch.settlement_date,
        gross_amount=batch.gross_amount, carrier_fees=batch.carrier_fees,
        net_amount=batch.net_amount, status=batch.status, notes=batch.notes,
        lines=[SettlementLineResponse.model_validate(line) for line in lines],
    )


@router.post("/settlements", response_model=SettlementBatchResponse, status_code=201, dependencies=[Depends(require_permission("shipping.write"))])
def create_settlement(p: SettlementBatchCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, p.company_id, current_user)
    carrier = db.scalar(select(ShippingCarrier).where(ShippingCarrier.id == p.carrier_id, ShippingCarrier.company_id == p.company_id, ShippingCarrier.is_active.is_(True)))
    if carrier is None:
        raise HTTPException(404, "Carrier not found")
    if db.scalar(select(ShippingSettlementBatch).where(ShippingSettlementBatch.company_id == p.company_id, ShippingSettlementBatch.reference == p.reference)):
        raise HTTPException(409, "Settlement reference already exists")

    shipment_ids = [line.shipment_id for line in p.lines]
    if len(shipment_ids) != len(set(shipment_ids)):
        raise HTTPException(422, "A shipment may appear only once in a settlement")
    shipments_by_id = {s.id: s for s in db.scalars(select(Shipment).where(Shipment.id.in_(shipment_ids), Shipment.company_id == p.company_id).with_for_update()).all()}
    if len(shipments_by_id) != len(shipment_ids):
        raise HTTPException(404, "One or more shipments were not found in the company")

    gross = Decimal("0")
    fees = Decimal("0")
    batch = ShippingSettlementBatch(company_id=p.company_id, carrier_id=p.carrier_id, reference=p.reference, settlement_date=p.settlement_date, notes=p.notes)
    db.add(batch)
    db.flush()
    for line in p.lines:
        s = shipments_by_id[line.shipment_id]
        if s.carrier_id != p.carrier_id:
            raise HTTPException(422, "Shipment carrier does not match settlement carrier")
        if s.status not in {"delivered", "returned"}:
            raise HTTPException(409, f"Shipment {s.id} is not eligible for settlement")
        if db.scalar(select(ShippingShipmentSettlement).where(ShippingShipmentSettlement.shipment_id == s.id).with_for_update()):
            raise HTTPException(409, f"Shipment {s.id} is already settled")
        expected = s.cod_amount if s.cod_amount > 0 else s.shipping_fee
        net = max(Decimal("0"), line.collected_amount - line.carrier_fee)
        variance = line.collected_amount - expected
        db.add(ShippingShipmentSettlement(batch_id=batch.id, shipment_id=s.id, expected_amount=expected, collected_amount=line.collected_amount, carrier_fee=line.carrier_fee, net_amount=net, variance=variance, reconciled=(variance == 0)))
        gross += line.collected_amount
        fees += line.carrier_fee
    batch.gross_amount = gross
    batch.carrier_fees = fees
    batch.net_amount = gross - fees
    if batch.net_amount < 0:
        raise HTTPException(422, "Carrier fees cannot exceed collected amount")
    db.commit()
    db.refresh(batch)
    return _settlement_response(db, batch)


@router.get("/settlements", response_model=list[SettlementBatchResponse])
def list_settlements(company_id: int = Query(..., gt=0), status: str | None = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    q = select(ShippingSettlementBatch).where(ShippingSettlementBatch.company_id == company_id)
    if status:
        q = q.where(ShippingSettlementBatch.status == status)
    batches = list(db.scalars(q.order_by(ShippingSettlementBatch.id.desc())).all())
    return [_settlement_response(db, b) for b in batches]


@router.post("/settlements/{batch_id}/reconcile", response_model=SettlementBatchResponse, dependencies=[Depends(require_permission("shipping.post"))])
def reconcile_settlement(batch_id: int, company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    batch = db.scalar(select(ShippingSettlementBatch).where(ShippingSettlementBatch.id == batch_id, ShippingSettlementBatch.company_id == company_id).with_for_update())
    if batch is None:
        raise HTTPException(404, "Settlement batch not found")
    if batch.status != "open":
        raise HTTPException(409, "Only open settlement batches can be reconciled")
    lines = list(db.scalars(select(ShippingShipmentSettlement).where(ShippingShipmentSettlement.batch_id == batch.id).with_for_update()).all())
    if not lines:
        raise HTTPException(409, "Settlement batch has no lines")
    if any(line.variance != 0 for line in lines):
        raise HTTPException(409, "Settlement has unreconciled variances")
    for line in lines:
        line.reconciled = True
    batch.status = "reconciled"
    db.commit()
    db.refresh(batch)
    return _settlement_response(db, batch)


@router.post("/settlements/{batch_id}/cancel", response_model=SettlementBatchResponse, dependencies=[Depends(require_permission("shipping.post"))])
def cancel_settlement(batch_id: int, company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    batch = db.scalar(select(ShippingSettlementBatch).where(ShippingSettlementBatch.id == batch_id, ShippingSettlementBatch.company_id == company_id).with_for_update())
    if batch is None:
        raise HTTPException(404, "Settlement batch not found")
    if batch.status != "open":
        raise HTTPException(409, "Only open settlement batches can be cancelled")
    batch.status = "cancelled"
    db.commit()
    db.refresh(batch)
    return _settlement_response(db, batch)
