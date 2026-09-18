from datetime import date
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.context import get_effective_tenant_id
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.accounting.chart_of_accounts.models import AccountCombination
from app.modules.accounting.journals.models import AccountingJournal
from app.modules.branches.models import Branch
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.saas.entitlements import require_module
from app.modules.commerce.models import SalesDocument
from app.modules.shipping.models import ShippingCarrier, ShippingMethod, Shipment
from app.modules.shipping.cost_models import ShippingShipmentCost
from app.modules.shipping.schemas import CarrierCreate, CarrierResponse, MethodCreate, MethodResponse, ShipmentCreate, ShipmentResponse
from app.modules.shipping.pricing_schemas import ShippingCostInput
from app.modules.shipping.pricing_service import shipping_pricing_service
from app.modules.shipping.status_service import shipping_status_service

router = APIRouter(prefix="/shipping", tags=["Shipping"], dependencies=[Depends(require_permission("shipping.access")), Depends(require_module("shipping"))])


def _tenant_id(user: User) -> int:
    return get_effective_tenant_id(user)


def _company_for_user(db: Session, company_id: int, user: User):
    tenant_id = _tenant_id(user)
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == tenant_id))
    if company is None:
        raise HTTPException(403, "Company is outside the current tenant")
    if not company.is_active:
        raise HTTPException(409, "Company is inactive")
    return company


def _validate_account(db: Session, company_id: int, account_id: int | None, label: str):
    if account_id is None:
        return
    account = db.scalar(select(AccountCombination).where(AccountCombination.id == account_id, AccountCombination.company_id == company_id, AccountCombination.is_active.is_(True)))
    if account is None:
        raise HTTPException(422, f"{label} does not belong to the company or is inactive")


def _validate_journal_and_branch(db: Session, company_id: int, journal_id: int | None, branch_id: int | None, tenant_id: int):
    if journal_id is None or branch_id is None:
        return
    journal = db.scalar(select(AccountingJournal).where(AccountingJournal.id == journal_id, AccountingJournal.company_id == company_id, AccountingJournal.tenant_id == tenant_id, AccountingJournal.is_active.is_(True)))
    if journal is None:
        raise HTTPException(422, "Settlement journal does not belong to the company or is inactive")
    branch = db.scalar(select(Branch).where(Branch.id == branch_id, Branch.company_id == company_id, Branch.tenant_id == tenant_id, Branch.is_active.is_(True)))
    if branch is None:
        raise HTTPException(422, "Settlement branch does not belong to the company or is inactive")


@router.post("/carriers", response_model=CarrierResponse, status_code=201, dependencies=[Depends(require_permission("shipping.write"))])
def carrier(payload: CarrierCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    company = _company_for_user(db, payload.company_id, current_user)
    if db.scalar(select(ShippingCarrier).where(ShippingCarrier.company_id == payload.company_id, ShippingCarrier.code == payload.code)):
        raise HTTPException(409, "Carrier code already exists")
    _validate_account(db, company.id, payload.settlement_account_id, "Carrier settlement account")
    _validate_account(db, company.id, payload.cash_account_id, "Carrier cash account")
    _validate_account(db, company.id, payload.fee_account_id, "Carrier fee account")
    _validate_journal_and_branch(db, company.id, payload.settlement_journal_id, payload.branch_id, _tenant_id(current_user))
    if not all((payload.settlement_account_id, payload.cash_account_id, payload.fee_account_id)):
        raise HTTPException(422, "Settlement, cash and fee accounts must be configured together")
    if (payload.settlement_journal_id is None) != (payload.branch_id is None):
        raise HTTPException(422, "Settlement journal and branch must be configured together")
    obj = ShippingCarrier(**payload.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


@router.get("/carriers", response_model=list[CarrierResponse])
def carriers(company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    return list(db.scalars(select(ShippingCarrier).where(ShippingCarrier.company_id == company_id, ShippingCarrier.is_active.is_(True)).order_by(ShippingCarrier.name)).all())


@router.post("/methods", response_model=MethodResponse, status_code=201, dependencies=[Depends(require_permission("shipping.write"))])
def method(payload: MethodCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tenant_id = _tenant_id(current_user)
    carrier_obj = db.scalar(select(ShippingCarrier).join(Company, Company.id == ShippingCarrier.company_id).where(ShippingCarrier.id == payload.carrier_id, Company.tenant_id == tenant_id, ShippingCarrier.is_active.is_(True)))
    if carrier_obj is None:
        raise HTTPException(404, "Carrier not found")
    if payload.payment_method not in {"prepaid", "cod", "mixed"}:
        raise HTTPException(422, "Invalid shipping payment method")
    if payload.payment_method == "prepaid" and payload.cod_fee_percent:
        raise HTTPException(422, "COD fee is not valid for prepaid-only methods")
    _validate_account(db, carrier_obj.company_id, payload.payment_account_id, "Shipping payment account")
    obj = ShippingMethod(carrier_id=carrier_obj.id, **payload.model_dump(exclude={"carrier_id"}))
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


@router.get("/methods", response_model=list[MethodResponse])
def methods(carrier_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tenant_id = _tenant_id(current_user)
    carrier_obj = db.scalar(select(ShippingCarrier).join(Company, Company.id == ShippingCarrier.company_id).where(ShippingCarrier.id == carrier_id, Company.tenant_id == tenant_id))
    if carrier_obj is None:
        raise HTTPException(404, "Carrier not found")
    return list(db.scalars(select(ShippingMethod).where(ShippingMethod.carrier_id == carrier_id).order_by(ShippingMethod.name)).all())


@router.post("/shipments", response_model=ShipmentResponse, status_code=201, dependencies=[Depends(require_permission("shipping.write"))])
def shipment(payload: ShipmentCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, payload.company_id, current_user)
    method_obj = db.scalar(select(ShippingMethod).join(ShippingCarrier, ShippingCarrier.id == ShippingMethod.carrier_id).where(ShippingMethod.id == payload.method_id, ShippingMethod.carrier_id == payload.carrier_id, ShippingCarrier.company_id == payload.company_id, ShippingCarrier.is_active.is_(True)))
    if method_obj is None:
        raise HTTPException(400, "Invalid carrier/method for company")
    if payload.sales_document_id is not None:
        sales_document = db.scalar(select(SalesDocument).where(
            SalesDocument.id == payload.sales_document_id,
            SalesDocument.company_id == payload.company_id,
        ))
        if sales_document is None:
            raise HTTPException(422, "Sales document does not belong to the company")
        if sales_document.document_type not in {"order", "delivery", "invoice"}:
            raise HTTPException(422, "Only sales orders, deliveries, or invoices can be linked to a shipment")
        if sales_document.status in {"cancelled"}:
            raise HTTPException(409, "Cannot create a shipment for a cancelled sales document")
    if payload.cod_amount and method_obj.payment_method == "prepaid":
        raise HTTPException(422, "COD amount is not allowed for prepaid shipping")
    fee = payload.shipping_fee if payload.shipping_fee > 0 else method_obj.base_fee
    if method_obj.payment_method in {"cod", "mixed"} and payload.cod_amount:
        fee += payload.cod_amount * method_obj.cod_fee_percent / 100

    shipment_date = payload.shipment_date or date.today()
    order_date = payload.order_date
    if order_date is None and payload.sales_document_id is not None:
        order_date = sales_document.document_date

    pricing_result = None
    try:
        pricing_result = shipping_pricing_service.calculate(
            db,
            ShippingCostInput(
                company_id=payload.company_id,
                carrier_id=payload.carrier_id,
                calculation_date=shipment_date,
                zone_code=payload.zone_code,
                weight_kg=payload.weight_kg,
                pieces=payload.pieces,
                order_value=payload.order_value,
                cod_amount=payload.cod_amount,
                cod_collected=payload.cod_collected,
                card_amount=payload.card_amount,
                remote_area=payload.remote_area,
                storage_days=payload.storage_days,
                exchange_requested=payload.exchange_requested,
            ),
        )
        fee = pricing_result.total_cost
    except ValueError:
        pass

    obj = Shipment(
        company_id=payload.company_id,
        carrier_id=payload.carrier_id,
        method_id=payload.method_id,
        sales_document_id=payload.sales_document_id,
        tracking_no=payload.tracking_no,
        order_date=order_date,
        shipment_date=shipment_date,
        zone_code=payload.zone_code,
        weight_kg=payload.weight_kg,
        pieces=payload.pieces,
        order_value=payload.order_value,
        cod_amount=payload.cod_amount,
        cod_collected=payload.cod_collected,
        card_amount=payload.card_amount,
        remote_area=payload.remote_area,
        storage_days=payload.storage_days,
        exchange_requested=payload.exchange_requested,
        shipping_fee=fee,
        customer_shipping_fee=payload.customer_shipping_fee,
        customer_name=payload.customer_name,
        phone=payload.phone,
        address=payload.address,
        notes=payload.notes,
    )
    db.add(obj)
    db.flush()

    if pricing_result is not None:
        db.add(ShippingShipmentCost(
            shipment_id=obj.id,
            profile_id=pricing_result.profile_id,
            order_date=order_date,
            shipment_date=shipment_date,
            calculated_at=shipment_date,
            base_shipping=pricing_result.base_shipping,
            cod_fee=pricing_result.cod_fee,
            cod_collected_fee=pricing_result.cod_collected_fee,
            card_fee=pricing_result.card_fee,
            remote_fee=pricing_result.surcharge_remote,
            rto_fee=pricing_result.surcharge_rto,
            exchange_fee=pricing_result.surcharge_exchange,
            storage_fee=pricing_result.storage_fee,
            other_fees=pricing_result.other_fees,
            minimum_adjustment=pricing_result.minimum_adjustment,
            total_cost=pricing_result.total_cost,
            calculation_breakdown=json.dumps(pricing_result.breakdown, ensure_ascii=False),
        ))
    db.commit(); db.refresh(obj)
    return obj


@router.get("/shipments", response_model=list[ShipmentResponse])
def shipments(company_id: int = Query(..., gt=0), status: str | None = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    stmt = select(Shipment).where(Shipment.company_id == company_id)
    if status:
        stmt = stmt.where(Shipment.status == status)
    return list(db.scalars(stmt.order_by(Shipment.id.desc())).all())


@router.post("/shipments/{shipment_id}/status", response_model=ShipmentResponse, dependencies=[Depends(require_permission("shipping.write"))])
def status(shipment_id: int, value: str = Query(...), company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company_for_user(db, company_id, current_user)
    obj = db.scalar(select(Shipment).where(Shipment.id == shipment_id, Shipment.company_id == company_id).with_for_update())
    if obj is None:
        raise HTTPException(404, "Shipment not found")
    if value == obj.status:
        return obj
    try:
        shipping_status_service.apply_transition(db, obj, value)
        db.commit(); db.refresh(obj)
        return obj
    except ValueError as exc:
        db.rollback()
        raise HTTPException(409, str(exc)) from exc
