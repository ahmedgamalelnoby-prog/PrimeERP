from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.sales.quotations.schemas import QuotationCreate, QuotationResponse
from app.modules.sales.quotations.service import sales_quotation_service

router = APIRouter(prefix="/sales/quotations", tags=["Sales Quotations"])

@router.get("", response_model=list[QuotationResponse])
def list_quotations(company_id: int = Query(gt=0), db: Session = Depends(get_db)):
    return sales_quotation_service.list(db, company_id)

@router.get("/{quotation_id}", response_model=QuotationResponse)
def get_quotation(quotation_id: int, company_id: int = Query(gt=0), db: Session = Depends(get_db)):
    quotation = sales_quotation_service.get(db, company_id, quotation_id)
    if quotation is None:
        raise HTTPException(404, "Quotation not found")
    return quotation

@router.post("", response_model=QuotationResponse, status_code=201)
def create_quotation(payload: QuotationCreate, db: Session = Depends(get_db)):
    try:
        quotation = sales_quotation_service.create(db, payload)
        db.commit(); db.refresh(quotation)
        return quotation
    except ValueError as exc:
        db.rollback(); raise HTTPException(400, str(exc)) from exc

@router.post("/{quotation_id}/{target}", response_model=QuotationResponse)
def transition_quotation(quotation_id: int, target: str, company_id: int = Query(gt=0), db: Session = Depends(get_db)):
    try:
        quotation = sales_quotation_service.transition(db, company_id, quotation_id, target)
        db.commit(); db.refresh(quotation)
        return quotation
    except ValueError as exc:
        db.rollback(); raise HTTPException(400, str(exc)) from exc
