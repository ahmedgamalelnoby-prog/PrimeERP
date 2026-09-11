from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.treasury.schemas import PaymentMethodCreate, PaymentMethodResponse, PaymentCreate, PaymentResponse, PaymentReverseRequest
from app.modules.treasury.service import treasury_service

router = APIRouter(prefix="/treasury", tags=["Treasury"])

@router.get("/payment-methods", response_model=list[PaymentMethodResponse])
def list_methods(company_id: int = Query(gt=0), db: Session = Depends(get_db)):
    return treasury_service.list_methods(db, company_id)

@router.post("/payment-methods", response_model=PaymentMethodResponse, status_code=201)
def create_method(payload: PaymentMethodCreate, db: Session = Depends(get_db)):
    try:
        result = treasury_service.create_method(db, payload); db.commit(); db.refresh(result); return result
    except ValueError as exc:
        db.rollback(); raise HTTPException(400, str(exc)) from exc

@router.get("/payments", response_model=list[PaymentResponse])
def list_payments(company_id: int = Query(gt=0), party_type: str | None = None, direction: str | None = None, db: Session = Depends(get_db)):
    return treasury_service.list_payments(db, company_id, party_type, direction)

@router.post("/payments", response_model=PaymentResponse, status_code=201)
def create_payment(payload: PaymentCreate, db: Session = Depends(get_db)):
    try:
        result = treasury_service.create_payment(db, payload); db.commit(); db.refresh(result); return result
    except ValueError as exc:
        db.rollback(); raise HTTPException(400, str(exc)) from exc

@router.post("/payments/{payment_id}/reverse", response_model=PaymentResponse)
def reverse_payment(payment_id: int, payload: PaymentReverseRequest | None = None, company_id: int = Query(gt=0), db: Session = Depends(get_db)):
    try:
        result = treasury_service.reverse_payment(db, company_id, payment_id, payload.notes if payload else None); db.commit(); db.refresh(result); return result
    except ValueError as exc:
        db.rollback(); raise HTTPException(409, str(exc)) from exc
