from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.shipping.cost_models import ShippingShipmentCost
from app.modules.shipping.models import ShippingCarrier, Shipment
from app.modules.shipping.settlement_models import ShippingShipmentSettlement
from app.modules.shipping.status_models import ShippingFinancialEvent
from app.modules.saas.entitlements import require_module

router = APIRouter(
    prefix="/shipping/reports",
    tags=["Shipping Reports"],
    dependencies=[Depends(require_permission("shipping.access")), Depends(require_module("shipping"))],
)


def _company(db: Session, company_id: int, user: User):
    if user.tenant_id is None:
        raise HTTPException(403, "User is not assigned to a tenant")
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == user.tenant_id, Company.is_active.is_(True)))
    if company is None:
        raise HTTPException(403, "Company is outside the current tenant or inactive")
    return company


def _filtered_shipments(db: Session, company_id: int, carrier_id: int | None, date_from: date | None, date_to: date | None, date_basis: str):
    stmt = select(Shipment, ShippingCarrier.name, ShippingShipmentCost).join(ShippingCarrier, ShippingCarrier.id == Shipment.carrier_id).outerjoin(ShippingShipmentCost, ShippingShipmentCost.shipment_id == Shipment.id).where(Shipment.company_id == company_id)
    if carrier_id:
        stmt = stmt.where(Shipment.carrier_id == carrier_id)
    column = Shipment.order_date if date_basis == "order" else Shipment.shipment_date
    if date_from:
        stmt = stmt.where(column >= date_from)
    if date_to:
        stmt = stmt.where(column <= date_to)
    return db.execute(stmt.order_by(Shipment.id.desc())).all()


def _events(db: Session, shipment_id: int):
    return db.scalars(select(ShippingFinancialEvent).where(ShippingFinancialEvent.shipment_id == shipment_id)).all()


def _ledger_for_shipment(db: Session, shipment_id: int):
    expected_cod = Decimal("0")
    carrier_payable = Decimal("0")
    revenue = Decimal("0")
    for event in _events(db, shipment_id):
        amount = Decimal(event.amount or 0)
        if event.event_type == "create_cod_receivable":
            expected_cod += amount
        elif event.event_type == "reverse_cod_receivable":
            expected_cod -= amount
        elif event.event_type in {"recognize_shipping_cost", "recognize_cod_fee", "recognize_card_fee", "recognize_return_cost"}:
            carrier_payable += amount
        elif event.event_type in {"recognize_revenue", "recognize_shipping_revenue"}:
            revenue += amount
        elif event.event_type in {"reverse_revenue", "reverse_shipping_revenue"}:
            revenue -= amount
    return expected_cod, carrier_payable, revenue


@router.get("/carrier-position")
def carrier_position(company_id: int = Query(..., gt=0), carrier_id: int | None = Query(default=None, gt=0), date_from: date | None = None, date_to: date | None = None, date_basis: str = Query(default="shipment", pattern="^(order|shipment)$"), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, company_id, current_user)
    rows = _filtered_shipments(db, company_id, carrier_id, date_from, date_to, date_basis)
    by_carrier = {}
    for shipment, carrier_name, cost in rows:
        bucket = by_carrier.setdefault(shipment.carrier_id, {
            "carrier_id": shipment.carrier_id, "carrier_name": carrier_name,
            "cod_receivable": Decimal("0"), "carrier_payable": Decimal("0"),
            "settled_net": Decimal("0"), "settled_gross": Decimal("0"), "settled_fees": Decimal("0"),
            "revenue": Decimal("0"), "shipment_count": 0, "unsettled_count": 0,
        })
        bucket["shipment_count"] += 1
        expected_cod, carrier_payable, revenue = _ledger_for_shipment(db, shipment.id)
        bucket["cod_receivable"] += expected_cod
        bucket["carrier_payable"] += carrier_payable
        bucket["revenue"] += revenue
        settled = db.scalar(select(ShippingShipmentSettlement).where(ShippingShipmentSettlement.shipment_id == shipment.id))
        if settled is None:
            bucket["unsettled_count"] += 1
        else:
            bucket["settled_gross"] += Decimal(settled.collected_amount or 0)
            bucket["settled_net"] += Decimal(settled.net_amount or 0)
            bucket["settled_fees"] += Decimal(settled.carrier_fee or 0)

    result = []
    for bucket in by_carrier.values():
        # Positive means the carrier still owes the company. Negative means the
        # company still owes the carrier. Carrier fees deducted from a remittance
        # settle the corresponding carrier payable, so they are added back here.
        bucket["net_position"] = (
            bucket["cod_receivable"]
            - bucket["settled_net"]
            - bucket["carrier_payable"]
            + bucket["settled_fees"]
        )
        bucket["position"] = "carrier_owes_company" if bucket["net_position"] > 0 else ("company_owes_carrier" if bucket["net_position"] < 0 else "settled")
        for key in ("cod_receivable", "carrier_payable", "settled_gross", "settled_fees", "settled_net", "revenue", "net_position"):
            bucket[key] = str(bucket[key].quantize(Decimal("0.01")))
        result.append(bucket)
    return result


@router.get("/shipment-reconciliation")
def shipment_reconciliation(company_id: int = Query(..., gt=0), carrier_id: int | None = Query(default=None, gt=0), date_from: date | None = None, date_to: date | None = None, date_basis: str = Query(default="shipment", pattern="^(order|shipment)$"), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, company_id, current_user)
    rows = _filtered_shipments(db, company_id, carrier_id, date_from, date_to, date_basis)
    result = []
    for shipment, carrier_name, cost in rows:
        expected_cod, carrier_payable, revenue = _ledger_for_shipment(db, shipment.id)
        settled = db.scalar(select(ShippingShipmentSettlement).where(ShippingShipmentSettlement.shipment_id == shipment.id))
        result.append({
            "shipment_id": shipment.id, "tracking_no": shipment.tracking_no,
            "carrier_id": shipment.carrier_id, "carrier_name": carrier_name, "status": shipment.status,
            "order_date": shipment.order_date, "shipment_date": shipment.shipment_date,
            "cod_amount": str(Decimal(shipment.cod_amount or 0).quantize(Decimal("0.01"))),
            "cod_receivable": str(expected_cod.quantize(Decimal("0.01"))),
            "carrier_payable": str(carrier_payable.quantize(Decimal("0.01"))),
            "revenue": str(revenue.quantize(Decimal("0.01"))),
            "settled": settled is not None,
            "collected_amount": str(Decimal(settled.collected_amount or 0).quantize(Decimal("0.01"))) if settled else None,
            "carrier_fee": str(Decimal(settled.carrier_fee or 0).quantize(Decimal("0.01"))) if settled else None,
            "net_settlement": str(Decimal(settled.net_amount or 0).quantize(Decimal("0.01"))) if settled else None,
            "variance": str(Decimal(settled.variance or 0).quantize(Decimal("0.01"))) if settled else None,
        })
    return result
