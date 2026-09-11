from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.inventory.adjustments.schemas import AdjustmentCreate, AdjustmentResponse
from app.modules.inventory.adjustments.service import inventory_adjustment_service

router = APIRouter(prefix="/inventory/adjustments", tags=["Inventory Adjustments"])


def _error(exc: ValueError):
    raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", response_model=list[AdjustmentResponse])
def list_adjustments(company_id: int = Query(..., gt=0), status: str | None = Query(default=None), db: Session = Depends(get_db)):
    return inventory_adjustment_service.list(db, company_id=company_id, status=status)


@router.post("", response_model=AdjustmentResponse, status_code=201)
def create_adjustment(payload: AdjustmentCreate, db: Session = Depends(get_db)):
    try:
        return inventory_adjustment_service.create(db, payload)
    except ValueError as exc:
        _error(exc)


@router.post("/{adjustment_id}/approve", response_model=AdjustmentResponse)
def approve_adjustment(adjustment_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db)):
    try:
        return inventory_adjustment_service.approve(db, company_id=company_id, adjustment_id=adjustment_id)
    except ValueError as exc:
        _error(exc)


@router.post("/{adjustment_id}/post", response_model=AdjustmentResponse)
def post_adjustment(adjustment_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db)):
    try:
        adjustment = inventory_adjustment_service.post(db, company_id=company_id, adjustment_id=adjustment_id)
        db.commit()
        db.refresh(adjustment)
        return adjustment
    except ValueError as exc:
        db.rollback()
        _error(exc)


@router.post("/{adjustment_id}/cancel", response_model=AdjustmentResponse)
def cancel_adjustment(adjustment_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db)):
    try:
        return inventory_adjustment_service.cancel(db, company_id=company_id, adjustment_id=adjustment_id)
    except ValueError as exc:
        _error(exc)
