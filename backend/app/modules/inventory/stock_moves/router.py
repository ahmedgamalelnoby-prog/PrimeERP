from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.inventory.stock_moves.schemas import StockMoveCreate, StockMoveResponse
from app.modules.inventory.stock_moves.service import inventory_stock_move_service

router = APIRouter(prefix="/inventory/stock-moves", tags=["Inventory Stock Moves"])


@router.get("", response_model=list[StockMoveResponse])
def list_stock_moves(
    company_id: int = Query(..., gt=0),
    item_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
):
    return inventory_stock_move_service.list(db, company_id, item_id)


@router.post("", response_model=StockMoveResponse, status_code=201)
def create_stock_move(payload: StockMoveCreate, db: Session = Depends(get_db)):
    try:
        return inventory_stock_move_service.create_draft(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{move_id}/post", response_model=StockMoveResponse)
def post_stock_move(
    move_id: int,
    company_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
):
    try:
        move = inventory_stock_move_service.post(db, company_id=company_id, move_id=move_id)
        db.commit()
        db.refresh(move)
        return move
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
