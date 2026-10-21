from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.platform.customers.schemas import CustomerCreate, CustomerResponse, CustomerUpdate
from app.modules.platform.customers.service import customer_service

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("", response_model=list[CustomerResponse])
def list_customers(company_id: int = Query(gt=0), db: Session = Depends(get_db)):
    return customer_service.list(db, company_id)


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int, company_id: int = Query(gt=0), db: Session = Depends(get_db)):
    customer = customer_service.get(db, company_id, customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.post("", response_model=CustomerResponse, status_code=201)
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db)):
    try:
        customer = customer_service.create(db, payload)
        db.commit(); db.refresh(customer)
        return customer
    except ValueError as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/{customer_id}", response_model=CustomerResponse)
def update_customer(customer_id: int, payload: CustomerUpdate, company_id: int = Query(gt=0), db: Session = Depends(get_db)):
    try:
        customer = customer_service.update(db, company_id, customer_id, payload)
        db.commit(); db.refresh(customer)
        return customer
    except ValueError as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc
