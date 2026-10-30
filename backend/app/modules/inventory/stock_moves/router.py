from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, aliased

from app.core.context import get_effective_tenant_id
from app.core.permissions import require_permission
from app.modules.branches.access import accessible_branch_ids, can_manage_all_branches, require_branch_access
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.inventory.locations.models import InventoryLocation
from app.modules.inventory.stock_moves.models import InventoryStockMove
from app.modules.inventory.warehouses.models import InventoryWarehouse
from app.modules.inventory.stock_moves.schemas import InventoryAccountingConfigCreate, InventoryAccountingConfigResponse, StockMoveCreate, StockMoveResponse
from app.modules.inventory.stock_moves.service import inventory_stock_move_service

router = APIRouter(prefix="/inventory/stock-moves", tags=["Inventory Stock Moves"])


def _company_for_user(db: Session, company_id: int, user: User):
    if get_effective_tenant_id(user) is None:
        raise HTTPException(403, "User is not assigned to a tenant")
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == get_effective_tenant_id(user), Company.is_active.is_(True)))
    if company is None:
        raise HTTPException(403, "Company is outside the current tenant")
    return company


def _authorize_stock_move_locations(
    db: Session,
    user: User,
    company_id: int,
    source_location_id: int | None,
    destination_location_id: int | None,
) -> None:
    location_ids = {
        value for value in (source_location_id, destination_location_id)
        if value is not None
    }
    if not location_ids:
        raise HTTPException(status_code=422, detail="A stock movement must reference a location")

    rows = db.execute(
        select(InventoryLocation.id, InventoryWarehouse.branch_id)
        .join(InventoryWarehouse, InventoryWarehouse.id == InventoryLocation.warehouse_id)
        .where(
            InventoryLocation.id.in_(location_ids),
            InventoryLocation.company_id == company_id,
            InventoryWarehouse.company_id == company_id,
            InventoryWarehouse.tenant_id == get_effective_tenant_id(user),
        )
    ).all()
    if len(rows) != len(location_ids):
        raise HTTPException(status_code=404, detail="Stock location not found for company")

    branch_ids = {branch_id for _, branch_id in rows if branch_id is not None}
    if not branch_ids:
        if not can_manage_all_branches(db, user):
            raise HTTPException(status_code=403, detail="Tenant-wide branch management permission is required for central-only stock movements")
        return

    for branch_id in branch_ids:
        require_branch_access(db, user, branch_id)


def _authorize_existing_stock_move(
    db: Session,
    user: User,
    company_id: int,
    move_id: int,
) -> InventoryStockMove:
    move = db.scalar(
        select(InventoryStockMove).where(
            InventoryStockMove.id == move_id,
            InventoryStockMove.company_id == company_id,
        )
    )
    if move is None:
        raise HTTPException(status_code=404, detail="Stock movement not found")
    _authorize_stock_move_locations(
        db,
        user,
        company_id,
        move.source_location_id,
        move.destination_location_id,
    )
    return move


@router.get("", response_model=list[StockMoveResponse], dependencies=[Depends(require_permission("inventory.access"))])
def list_stock_moves(company_id: int = Query(..., gt=0), item_id: int | None = Query(default=None, gt=0), variant_id: int | None = Query(default=None, gt=0), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, user)
    if can_manage_all_branches(db, user):
        return inventory_stock_move_service.list(db, company_id, item_id, variant_id)
    allowed = accessible_branch_ids(db, user)
    source_location = aliased(InventoryLocation)
    destination_location = aliased(InventoryLocation)
    source_warehouse = aliased(InventoryWarehouse)
    destination_warehouse = aliased(InventoryWarehouse)
    stmt = (
        select(InventoryStockMove)
        .outerjoin(source_location, source_location.id == InventoryStockMove.source_location_id)
        .outerjoin(source_warehouse, source_warehouse.id == source_location.warehouse_id)
        .outerjoin(destination_location, destination_location.id == InventoryStockMove.destination_location_id)
        .outerjoin(destination_warehouse, destination_warehouse.id == destination_location.warehouse_id)
        .where(
            InventoryStockMove.company_id == company_id,
            or_(source_warehouse.branch_id.is_(None), source_warehouse.branch_id.in_(allowed)),
            or_(destination_warehouse.branch_id.is_(None), destination_warehouse.branch_id.in_(allowed)),
            or_(source_warehouse.branch_id.in_(allowed), destination_warehouse.branch_id.in_(allowed)),
        )
    )
    if item_id is not None:
        stmt = stmt.where(InventoryStockMove.item_id == item_id)
    if variant_id is not None:
        stmt = stmt.where(InventoryStockMove.variant_id == variant_id)
    return list(db.scalars(stmt.order_by(InventoryStockMove.id.desc())).all())


@router.get("/accounting-config", response_model=InventoryAccountingConfigResponse, dependencies=[Depends(require_permission("inventory.access"))])
def get_accounting_config(company_id: int = Query(..., gt=0), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, user)
    config = inventory_stock_move_service.get_accounting_config(db, tenant_id=get_effective_tenant_id(user), company_id=company_id)
    if config is None:
        raise HTTPException(404, "Inventory accounting configuration not found")
    return config


@router.put("/accounting-config", response_model=InventoryAccountingConfigResponse, dependencies=[Depends(require_permission("inventory.write"))])
def save_accounting_config(payload: InventoryAccountingConfigCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _company_for_user(db, payload.company_id, user)
    branch = require_branch_access(db, user, payload.branch_id)
    if branch.company_id != payload.company_id:
        raise HTTPException(status_code=404, detail="Branch not found for company")
    try:
        config = inventory_stock_move_service.save_accounting_config(db, tenant_id=get_effective_tenant_id(user), payload=payload)
        db.commit()
        db.refresh(config)
        return config
    except ValueError as exc:
        db.rollback()
        raise HTTPException(400, str(exc)) from exc


@router.post("", response_model=StockMoveResponse, status_code=201, dependencies=[Depends(require_permission("inventory.write"))])
def create_stock_move(payload: StockMoveCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _company_for_user(db, payload.company_id, user)
    _authorize_stock_move_locations(
        db,
        user,
        payload.company_id,
        payload.source_location_id,
        payload.destination_location_id,
    )
    try:
        move = inventory_stock_move_service.create_draft(db, payload)
        db.commit()
        db.refresh(move)
        return move
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{move_id}/post", response_model=StockMoveResponse, dependencies=[Depends(require_permission("inventory.post"))])
def post_stock_move(move_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, user)
    _authorize_existing_stock_move(db, user, company_id, move_id)
    try:
        move = inventory_stock_move_service.post(db, tenant_id=get_effective_tenant_id(user), company_id=company_id, move_id=move_id, user_id=user.id)
        db.commit()
        db.refresh(move)
        return move
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{move_id}/reverse", response_model=StockMoveResponse, dependencies=[Depends(require_permission("inventory.post"))])
def reverse_stock_move(move_id: int, company_id: int = Query(..., gt=0), reversal_date: date | None = Query(default=None), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, user)
    _authorize_existing_stock_move(db, user, company_id, move_id)
    try:
        move = inventory_stock_move_service.reverse(db, tenant_id=get_effective_tenant_id(user), company_id=company_id, move_id=move_id, user_id=user.id, reversal_date=reversal_date)
        # journal_service.reverse commits as part of its atomic reversal. For
        # transfer movements there is no GL entry, so commit the physical reversal here.
        db.commit()
        db.refresh(move)
        return move
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
