from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.context import get_effective_tenant_id
from app.modules.branches.access import accessible_branch_ids, can_manage_all_branches, require_branch_access
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.saas.entitlements import require_module
from app.modules.shipping.models import ShippingCarrier
from app.modules.shipping.settlement_models import ShippingSettlementBatch, ShippingShipmentSettlement
from app.modules.shipping.settlement_schemas import SettlementBatchCreate, SettlementBatchResponse, SettlementLineResponse
from app.modules.shipping.settlement_service import shipping_settlement_service

router = APIRouter(
    prefix="/shipping/settlements",
    tags=["Shipping Settlements"],
    dependencies=[Depends(require_permission("shipping.access")), Depends(require_module("shipping"))],
)


def _company_for_user(db: Session, company_id: int, user: User):
    tenant_id = get_effective_tenant_id(user)
    if tenant_id is None:
        raise HTTPException(403, "User is not assigned to a tenant")
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == tenant_id, Company.is_active.is_(True)))
    if company is None:
        raise HTTPException(403, "Company is outside the current tenant")
    if not company.is_active:
        raise HTTPException(409, "Company is inactive")
    return company

def _require_carrier_access(db: Session, user: User, company_id: int, carrier_id: int):
    carrier = db.scalar(select(ShippingCarrier).where(
        ShippingCarrier.id == carrier_id,
        ShippingCarrier.company_id == company_id,
    ))
    if carrier is None:
        raise HTTPException(404, "Carrier not found for company")
    if carrier.branch_id is None:
        if not can_manage_all_branches(db, user):
            raise HTTPException(403, "Central carrier access requires tenant-wide branch management permission")
    else:
        require_branch_access(db, user, carrier.branch_id)
    return carrier


@router.post("", response_model=SettlementBatchResponse, status_code=201, dependencies=[Depends(require_permission("shipping.write"))])
def create_settlement(
    payload: SettlementBatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _company_for_user(db, payload.company_id, current_user)
    _require_carrier_access(db, current_user, payload.company_id, payload.carrier_id)
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
    stmt = select(ShippingSettlementBatch).join(
        ShippingCarrier, ShippingCarrier.id == ShippingSettlementBatch.carrier_id
    ).where(ShippingSettlementBatch.company_id == company_id)
    if carrier_id:
        _require_carrier_access(db, current_user, company_id, carrier_id)
        stmt = stmt.where(ShippingSettlementBatch.carrier_id == carrier_id)
    if not can_manage_all_branches(db, current_user):
        stmt = stmt.where(ShippingCarrier.branch_id.in_(accessible_branch_ids(db, current_user)))
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
    _require_carrier_access(db, current_user, company_id, batch.carrier_id)
    return list(db.scalars(select(ShippingShipmentSettlement).where(
        ShippingShipmentSettlement.batch_id == batch_id,
    ).order_by(ShippingShipmentSettlement.id)).all())
