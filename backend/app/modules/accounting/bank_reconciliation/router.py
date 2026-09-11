from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.accounting.bank_reconciliation.schemas import BankAccountCreate, BankAccountResponse, StatementLineCreate, StatementLineResponse
from app.modules.accounting.bank_reconciliation.service import bank_reconciliation_service

router = APIRouter(prefix="/accounting/bank-reconciliation", tags=["Bank Reconciliation"])

@router.get("/accounts", response_model=list[BankAccountResponse])
def accounts(company_id: int = Query(gt=0), db: Session = Depends(get_db)): return bank_reconciliation_service.list_accounts(db, company_id)

@router.post("/accounts", response_model=BankAccountResponse, status_code=201)
def create_account(payload: BankAccountCreate, db: Session = Depends(get_db)):
    try:
        x=bank_reconciliation_service.create_account(db,payload); db.commit(); db.refresh(x); return x
    except ValueError as exc: db.rollback(); raise HTTPException(400,str(exc)) from exc

@router.get("/statements", response_model=list[StatementLineResponse])
def statements(company_id: int = Query(gt=0), status: str | None = None, db: Session = Depends(get_db)): return bank_reconciliation_service.list_lines(db,company_id,status)

@router.post("/statements", response_model=StatementLineResponse, status_code=201)
def import_statement(payload: StatementLineCreate, db: Session = Depends(get_db)):
    try:
        x=bank_reconciliation_service.import_line(db,payload); db.commit(); db.refresh(x); return x
    except ValueError as exc: db.rollback(); raise HTTPException(400,str(exc)) from exc

@router.post("/statements/{line_id}/match/{payment_id}", response_model=StatementLineResponse)
def match(line_id: int, payment_id: int, company_id: int = Query(gt=0), db: Session = Depends(get_db)):
    try:
        x=bank_reconciliation_service.match_payment(db,company_id,line_id,payment_id); db.commit(); db.refresh(x); return x
    except ValueError as exc: db.rollback(); raise HTTPException(409,str(exc)) from exc
