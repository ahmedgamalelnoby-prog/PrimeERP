from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.context.access import require_company_access, require_branch_access
from app.core.context import get_optional_request_context
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.inventory.adjustments.schemas import AdjustmentCreate, AdjustmentResponse
from app.modules.inventory.adjustments.service import inventory_adjustment_service
from app.modules.inventory.adjustments.models import InventoryAdjustment
from app.modules.inventory.locations.models import InventoryLocation
from app.modules.inventory.warehouses.models import InventoryWarehouse

router = APIRouter(
    prefix="/inventory/adjustments",
    tags=["Inventory Adjustments"],
    dependencies=[Depends(require_permission("inventory.access"))],
)


def _company_for_user(db: Session, company_id: int, user: User) -> Company:
    return require_company_access(db, company_id, user)


def _error(exc: ValueError):
    raise HTTPException(status_code=400, detail=str(exc)) from exc


def _selected_branch(db: Session, company_id: int, user: User) -> int | None:
    if user.is_platform_admin:
        return None
    context = get_optional_request_context()
    if context is None or context.branch_id is None:
        raise HTTPException(400, "Select a branch using X-Branch-ID before accessing adjustments")
    require_branch_access(db, company_id, context.branch_id, user)
    return context.branch_id


def _assert_location_access(db: Session, company_id: int, location_id: int, user: User) -> None:
    location = db.scalar(select(InventoryLocation).where(
        InventoryLocation.id == location_id,
        InventoryLocation.company_id == company_id,
        InventoryLocation.is_active.is_(True),
    ))
    if location is None:
        raise HTTPException(404, "Stock location not found")
    warehouse = db.scalar(select(InventoryWarehouse).where(
        InventoryWarehouse.id == location.warehouse_id,
        InventoryWarehouse.company_id == company_id,
        InventoryWarehouse.is_active.is_(True),
    ))
    if warehouse is None:
        raise HTTPException(404, "Stock warehouse not found")
    if warehouse.branch_id is not None:
        require_branch_access(db, company_id, warehouse.branch_id, user)


def _assert_adjustment_access(db: Session, company_id: int, adjustment_id: int, user: User) -> None:
    adjustment = db.scalar(select(InventoryAdjustment).where(
        InventoryAdjustment.id == adjustment_id,
        InventoryAdjustment.company_id == company_id,
    ))
    if adjustment is None:
        raise HTTPException(404, "Adjustment not found")
    _assert_location_access(db, company_id, adjustment.location_id, user)


@router.get("", response_model=list[AdjustmentResponse])
def list_adjustments(
    company_id: int = Query(..., gt=0),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _company_for_user(db, company_id, current_user)
    branch_id = _selected_branch(db, company_id, current_user)
    return inventory_adjustment_service.list(db, company_id=company_id, status=status, branch_id=branch_id)


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
    _selected_branch(db, payload.company_id, current_user)
    _assert_location_access(db, payload.company_id, payload.location_id, current_user)
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
    _selected_branch(db, company_id, current_user)
    _assert_adjustment_access(db, company_id, adjustment_id, current_user)
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
    _selected_branch(db, company_id, current_user)
    _assert_adjustment_access(db, company_id, adjustment_id, current_user)
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
    _selected_branch(db, company_id, current_user)
    _assert_adjustment_access(db, company_id, adjustment_id, current_user)
    try:
        return inventory_adjustment_service.cancel(db, company_id=company_id, adjustment_id=adjustment_id)
    except ValueError as exc:
        _error(exc)
