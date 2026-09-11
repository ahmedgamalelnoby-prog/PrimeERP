from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.purchasing.purchase_orders.schemas import PurchaseOrderCreate, PurchaseOrderResponse
from app.modules.purchasing.purchase_orders.service import purchase_order_service

router = APIRouter(prefix="/purchasing/purchase-orders", tags=["Purchasing - Purchase Orders"])


def _error(exc: ValueError):
    return HTTPException(status_code=400, detail=str(exc))


@router.get("", response_model=list[PurchaseOrderResponse])
def list_orders(company_id: int = Query(gt=0), db: Session = Depends(get_db)):
    return purchase_order_service.list(db, company_id)


@router.get("/{order_id}", response_model=PurchaseOrderResponse)
def get_order(order_id: int, company_id: int = Query(gt=0), db: Session = Depends(get_db)):
    order = purchase_order_service.get(db, company_id, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return order


@router.post("", response_model=PurchaseOrderResponse, status_code=201)
def create_order(payload: PurchaseOrderCreate, db: Session = Depends(get_db)):
    try:
        order = purchase_order_service.create(db, payload)
        db.commit(); db.refresh(order)
        return order
    except ValueError as exc:
        db.rollback(); raise _error(exc) from exc


@router.post("/{order_id}/approve", response_model=PurchaseOrderResponse)
def approve_order(order_id: int, company_id: int = Query(gt=0), db: Session = Depends(get_db)):
    try:
        order = purchase_order_service.approve(db, company_id, order_id)
        db.commit(); db.refresh(order)
        return order
    except ValueError as exc:
        db.rollback(); raise _error(exc) from exc


@router.post("/{order_id}/cancel", response_model=PurchaseOrderResponse)
def cancel_order(order_id: int, company_id: int = Query(gt=0), db: Session = Depends(get_db)):
    try:
        order = purchase_order_service.cancel(db, company_id, order_id)
        db.commit(); db.refresh(order)
        return order
    except ValueError as exc:
        db.rollback(); raise _error(exc) from exc
