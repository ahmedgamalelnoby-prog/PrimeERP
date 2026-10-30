from app.core.context.access import require_company_access, require_branch_access
from app.core.context import get_optional_request_context
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.context import get_effective_tenant_id
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.inventory.stock_moves.schemas import InventoryAccountingConfigCreate, InventoryAccountingConfigResponse, StockMoveCreate, StockMoveResponse
from app.modules.inventory.stock_moves.service import inventory_stock_move_service
from app.modules.inventory.stock_moves.models import InventoryStockMove
from app.modules.inventory.locations.models import InventoryLocation
from app.modules.inventory.warehouses.models import InventoryWarehouse

router = APIRouter(prefix="/inventory/stock-moves", tags=["Inventory Stock Moves"])


def _company_for_user(db: Session, company_id: int, user: User):
    return require_company_access(db, company_id, user)
def _assert_location_pair_access(db: Session, company_id: int, location_ids, user: User) -> None:
    branch_ids = set()
    for location_id in location_ids:
        if location_id is None:
            continue
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
            branch_ids.add(warehouse.branch_id)
    if user.is_platform_admin or not branch_ids:
        return
    context = get_optional_request_context()
    if context is None or context.branch_id not in branch_ids:
        raise HTTPException(403, "Select one of the stock movement branches using X-Branch-ID")
    for branch_id in branch_ids:
        require_branch_access(db, company_id, branch_id, user, require_selected=False)


def _assert_move_access(db: Session, company_id: int, move: InventoryStockMove, user: User) -> None:
    _assert_location_pair_access(
        db, company_id, (move.source_location_id, move.destination_location_id), user
    )


@router.get("", response_model=list[StockMoveResponse], dependencies=[Depends(require_permission("inventory.access"))])
def list_stock_moves(company_id: int = Query(..., gt=0), item_id: int | None = Query(default=None, gt=0), variant_id: int | None = Query(default=None, gt=0), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, user)
    moves = inventory_stock_move_service.list(db, company_id, item_id, variant_id)
    if user.is_platform_admin:
        return moves
    visible = []
    for move in moves:
        try:
            _assert_move_access(db, company_id, move, user)
            visible.append(move)
        except HTTPException as exc:
            if exc.status_code not in {403, 404}:
                raise
    return visible


@router.get("/accounting-config", response_model=InventoryAccountingConfigResponse, dependencies=[Depends(require_permission("inventory.access"))])
def get_accounting_config(company_id: int = Query(..., gt=0), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, user)
    config = inventory_stock_move_service.get_accounting_config(db, tenant_id=get_effective_tenant_id(user), company_id=company_id)
    if config is None:
        raise HTTPException(404, "Inventory accounting configuration not found")
    require_branch_access(db, company_id, config.branch_id, user)
    return config


@router.put("/accounting-config", response_model=InventoryAccountingConfigResponse, dependencies=[Depends(require_permission("inventory.write"))])
def save_accounting_config(payload: InventoryAccountingConfigCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _company_for_user(db, payload.company_id, user)
    require_branch_access(db, payload.company_id, payload.branch_id, user)
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
    _assert_location_pair_access(db, payload.company_id, (payload.source_location_id, payload.destination_location_id), user)
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
    existing_move = db.scalar(select(InventoryStockMove).where(
        InventoryStockMove.id == move_id,
        InventoryStockMove.company_id == company_id,
    ))
    if existing_move is None:
        raise HTTPException(404, "Stock movement not found")
    _assert_move_access(db, company_id, existing_move, user)
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
    existing_move = db.scalar(select(InventoryStockMove).where(
        InventoryStockMove.id == move_id,
        InventoryStockMove.company_id == company_id,
    ))
    if existing_move is None:
        raise HTTPException(404, "Stock movement not found")
    _assert_move_access(db, company_id, existing_move, user)
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
