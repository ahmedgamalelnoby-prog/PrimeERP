from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.inventory.stock_moves.schemas import InventoryAccountingConfigCreate, InventoryAccountingConfigResponse, StockMoveCreate, StockMoveResponse
from app.modules.inventory.stock_moves.service import inventory_stock_move_service

router = APIRouter(prefix="/inventory/stock-moves", tags=["Inventory Stock Moves"])


def _company_for_user(db: Session, company_id: int, user: User):
    if user.tenant_id is None:
        raise HTTPException(403, "User is not assigned to a tenant")
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == user.tenant_id))
    if company is None:
        raise HTTPException(403, "Company is outside the current tenant")
    return company


@router.get("", response_model=list[StockMoveResponse], dependencies=[Depends(require_permission("inventory.access"))])
def list_stock_moves(company_id: int = Query(..., gt=0), item_id: int | None = Query(default=None, gt=0), variant_id: int | None = Query(default=None, gt=0), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, user)
    return inventory_stock_move_service.list(db, company_id, item_id, variant_id)


@router.get("/accounting-config", response_model=InventoryAccountingConfigResponse, dependencies=[Depends(require_permission("inventory.access"))])
def get_accounting_config(company_id: int = Query(..., gt=0), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, user)
    config = inventory_stock_move_service.get_accounting_config(db, tenant_id=user.tenant_id, company_id=company_id)
    if config is None:
        raise HTTPException(404, "Inventory accounting configuration not found")
    return config


@router.put("/accounting-config", response_model=InventoryAccountingConfigResponse, dependencies=[Depends(require_permission("inventory.write"))])
def save_accounting_config(payload: InventoryAccountingConfigCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _company_for_user(db, payload.company_id, user)
    try:
        config = inventory_stock_move_service.save_accounting_config(db, tenant_id=user.tenant_id, payload=payload)
        db.commit()
        db.refresh(config)
        return config
    except ValueError as exc:
        db.rollback()
        raise HTTPException(400, str(exc)) from exc


@router.post("", response_model=StockMoveResponse, status_code=201, dependencies=[Depends(require_permission("inventory.write"))])
def create_stock_move(payload: StockMoveCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _company_for_user(db, payload.company_id, user)
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
    try:
        move = inventory_stock_move_service.post(db, tenant_id=user.tenant_id, company_id=company_id, move_id=move_id, user_id=user.id)
        db.commit()
        db.refresh(move)
        return move
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
