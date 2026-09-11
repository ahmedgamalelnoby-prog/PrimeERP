from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.inventory.adjustments.schemas import AdjustmentCreate, AdjustmentResponse
from app.modules.inventory.adjustments.service import inventory_adjustment_service

router = APIRouter(
    prefix="/inventory/adjustments",
    tags=["Inventory Adjustments"],
    dependencies=[Depends(require_permission("inventory.access"))],
)


def _company_for_user(db: Session, company_id: int, user: User) -> Company:
    if user.tenant_id is None:
        raise HTTPException(status_code=403, detail="User is not assigned to a tenant")
    company = db.scalar(
        select(Company).where(
            Company.id == company_id,
            Company.tenant_id == user.tenant_id,
        )
    )
    if company is None:
        raise HTTPException(status_code=403, detail="Company is outside the current tenant")
    return company


def _error(exc: ValueError):
    raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", response_model=list[AdjustmentResponse])
def list_adjustments(
    company_id: int = Query(..., gt=0),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _company_for_user(db, company_id, current_user)
    return inventory_adjustment_service.list(db, company_id=company_id, status=status)


@router.post(
    "",
    response_model=AdjustmentResponse,
    status_code=201,
    dependencies=[Depends(require_permission("inventory.write"))],
)
def create_adjustment(
    payload: AdjustmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _company_for_user(db, payload.company_id, current_user)
    try:
        return inventory_adjustment_service.create(db, payload)
    except ValueError as exc:
        _error(exc)


@router.post(
    "/{adjustment_id}/approve",
    response_model=AdjustmentResponse,
    dependencies=[Depends(require_permission("inventory.post"))],
)
def approve_adjustment(
    adjustment_id: int,
    company_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _company_for_user(db, company_id, current_user)
    try:
        return inventory_adjustment_service.approve(db, company_id=company_id, adjustment_id=adjustment_id)
    except ValueError as exc:
        _error(exc)


@router.post(
    "/{adjustment_id}/post",
    response_model=AdjustmentResponse,
    dependencies=[Depends(require_permission("inventory.post"))],
)
def post_adjustment(
    adjustment_id: int,
    company_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _company_for_user(db, company_id, current_user)
    try:
        adjustment = inventory_adjustment_service.post(db, company_id=company_id, adjustment_id=adjustment_id)
        db.commit()
        db.refresh(adjustment)
        return adjustment
    except ValueError as exc:
        db.rollback()
        _error(exc)


@router.post(
    "/{adjustment_id}/cancel",
    response_model=AdjustmentResponse,
    dependencies=[Depends(require_permission("inventory.write"))],
)
def cancel_adjustment(
    adjustment_id: int,
    company_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _company_for_user(db, company_id, current_user)
    try:
        return inventory_adjustment_service.cancel(db, company_id=company_id, adjustment_id=adjustment_id)
    except ValueError as exc:
        _error(exc)
