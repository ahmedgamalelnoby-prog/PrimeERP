from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.sales.sales_core.schemas import SalesOrderCreate, SalesOrderResponse
from app.modules.sales.sales_core.service import sales_order_service

router = APIRouter(prefix="/sales/orders", tags=["Sales Orders"])


@router.get("", response_model=list[SalesOrderResponse])
def list_orders(company_id: int = Query(gt=0), db: Session = Depends(get_db)):
    return sales_order_service.list(db, company_id)


@router.get("/{order_id}", response_model=SalesOrderResponse)
def get_order(order_id: int, company_id: int = Query(gt=0), db: Session = Depends(get_db)):
    order = sales_order_service.get(db, company_id, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Sales order not found")
    return order


@router.post("", response_model=SalesOrderResponse, status_code=201)
def create_order(payload: SalesOrderCreate, db: Session = Depends(get_db)):
    try:
        order = sales_order_service.create(db, payload)
        db.commit(); db.refresh(order)
        return order
    except ValueError as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{order_id}/confirm", response_model=SalesOrderResponse)
def confirm_order(order_id: int, company_id: int = Query(gt=0), db: Session = Depends(get_db)):
    try:
        order = sales_order_service.confirm(db, company_id, order_id)
        db.commit(); db.refresh(order)
        return order
    except ValueError as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{order_id}/cancel", response_model=SalesOrderResponse)
def cancel_order(order_id: int, company_id: int = Query(gt=0), db: Session = Depends(get_db)):
    try:
        order = sales_order_service.cancel(db, company_id, order_id)
        db.commit(); db.refresh(order)
        return order
    except ValueError as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc
