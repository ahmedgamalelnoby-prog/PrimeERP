from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.saas.entitlements import require_module
from app.modules.shipping.settlement_models import ShippingSettlementBatch, ShippingShipmentSettlement
from app.modules.shipping.settlement_schemas import SettlementBatchCreate, SettlementBatchResponse, SettlementLineResponse
from app.modules.shipping.settlement_service import shipping_settlement_service

router = APIRouter(
    prefix="/shipping/settlements",
    tags=["Shipping Settlements"],
    dependencies=[Depends(require_permission("shipping.access")), Depends(require_module("shipping"))],
)


def _company_for_user(db: Session, company_id: int, user: User):
    if user.tenant_id is None:
        raise HTTPException(403, "User is not assigned to a tenant")
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == user.tenant_id))
    if company is None:
        raise HTTPException(403, "Company is outside the current tenant")
    if not company.is_active:
        raise HTTPException(409, "Company is inactive")
    return company


@router.post("", response_model=SettlementBatchResponse, status_code=201, dependencies=[Depends(require_permission("shipping.write"))])
def create_settlement(
    payload: SettlementBatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _company_for_user(db, payload.company_id, current_user)
    try:
        batch = shipping_settlement_service.create_batch(db, payload, user_id=current_user.id)
        db.commit()
        db.refresh(batch)
        return batch
    except (ValueError, HTTPException) as exc:
        db.rollback()
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("", response_model=list[SettlementBatchResponse])
def list_settlements(
    company_id: int = Query(..., gt=0),
    carrier_id: int | None = Query(default=None, gt=0),
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _company_for_user(db, company_id, current_user)
    stmt = select(ShippingSettlementBatch).where(ShippingSettlementBatch.company_id == company_id)
    if carrier_id:
        stmt = stmt.where(ShippingSettlementBatch.carrier_id == carrier_id)
    if status:
        stmt = stmt.where(ShippingSettlementBatch.status == status)
    return list(db.scalars(stmt.order_by(ShippingSettlementBatch.id.desc())).all())


@router.get("/{batch_id}/lines", response_model=list[SettlementLineResponse])
def settlement_lines(
    batch_id: int,
    company_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _company_for_user(db, company_id, current_user)
    batch = db.scalar(select(ShippingSettlementBatch).where(
        ShippingSettlementBatch.id == batch_id,
        ShippingSettlementBatch.company_id == company_id,
    ))
    if batch is None:
        raise HTTPException(404, "Settlement batch not found")
    return list(db.scalars(select(ShippingShipmentSettlement).where(
        ShippingShipmentSettlement.batch_id == batch_id,
    ).order_by(ShippingShipmentSettlement.id)).all())
