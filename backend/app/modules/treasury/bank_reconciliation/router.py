from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.treasury.bank_reconciliation.models import BankAccount, BankStatement, BankStatementLine, ReconciliationSession, ReconciliationMatch
from app.modules.treasury.bank_reconciliation.schemas import *
from app.modules.treasury.bank_reconciliation.service import ensure_company, create_account, create_statement, add_line, create_session, match, auto_match, close_session, unmatch, candidates

router=APIRouter(prefix="/treasury/reconciliation",tags=["Treasury Bank Reconciliation"],dependencies=[Depends(require_permission("treasury.access"))])

def fail(e): raise HTTPException(400,str(e))

@router.post("/accounts",response_model=BankAccountResponse,status_code=201,dependencies=[Depends(require_permission("treasury.write"))])
def account_create(payload:BankAccountCreate,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    try: o=create_account(db,payload,current_user); db.commit(); db.refresh(o); return o
    except ValueError as e: db.rollback(); fail(e)

@router.get("/accounts",response_model=list[BankAccountResponse])
def accounts(company_id:int=Query(...,gt=0),current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    ensure_company(db,company_id,current_user); return db.scalars(select(BankAccount).where(BankAccount.company_id==company_id,BankAccount.is_active.is_(True))).all()

@router.post("/statements",response_model=BankStatementResponse,status_code=201,dependencies=[Depends(require_permission("treasury.write"))])
def statement_create(payload:BankStatementCreate,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    try:o=create_statement(db,payload,current_user);db.commit();db.refresh(o);return o
    except ValueError as e:db.rollback();fail(e)

@router.get("/statements",response_model=list[BankStatementResponse])
def statements(company_id:int=Query(...,gt=0),bank_account_id:int=Query(...,gt=0),current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    ensure_company(db,company_id,current_user);return db.scalars(select(BankStatement).where(BankStatement.company_id==company_id,BankStatement.bank_account_id==bank_account_id).order_by(BankStatement.period_end.desc())).all()

@router.post("/statements/{statement_id}/lines",response_model=BankStatementLineResponse,status_code=201,dependencies=[Depends(require_permission("treasury.write"))])
def line_create(statement_id:int,payload:BankStatementLineCreate,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    st=db.scalar(select(BankStatement).where(BankStatement.id==statement_id))
    if not st: raise HTTPException(404,"Statement not found")
    try:ensure_company(db,st.company_id,current_user);o,created=add_line(db,st,payload);db.commit();db.refresh(o);return o
    except ValueError as e:db.rollback();fail(e)

@router.get("/statements/{statement_id}/lines",response_model=list[BankStatementLineResponse])
def lines(statement_id:int,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    st=db.get(BankStatement,statement_id)
    if not st: raise HTTPException(404,"Statement not found")
    ensure_company(db,st.company_id,current_user);return db.scalars(select(BankStatementLine).where(BankStatementLine.statement_id==statement_id).order_by(BankStatementLine.transaction_date, BankStatementLine.id)).all()

@router.post("/sessions",response_model=ReconciliationResponse,status_code=201,dependencies=[Depends(require_permission("treasury.write"))])
def session_create(payload:ReconciliationCreate,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    try:o=create_session(db,payload,current_user);db.commit();db.refresh(o);return o
    except ValueError as e:db.rollback();fail(e)

@router.get("/sessions",response_model=list[ReconciliationResponse])
def sessions(company_id:int=Query(...,gt=0),bank_account_id:int=Query(...,gt=0),current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    ensure_company(db,company_id,current_user);return db.scalars(select(ReconciliationSession).where(ReconciliationSession.company_id==company_id,ReconciliationSession.bank_account_id==bank_account_id).order_by(ReconciliationSession.id.desc())).all()

@router.post("/sessions/{session_id}/auto-match",response_model=AutoMatchResponse,dependencies=[Depends(require_permission("treasury.write"))])
def session_auto(session_id:int,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    s=db.get(ReconciliationSession,session_id)
    if not s: raise HTTPException(404,"Reconciliation session not found")
    try:ensure_company(db,s.company_id,current_user);m,c=auto_match(db,s,current_user);db.commit();return {"matched":m,"candidates":c}
    except ValueError as e:db.rollback();fail(e)

@router.post("/sessions/{session_id}/matches",response_model=MatchResponse,status_code=201,dependencies=[Depends(require_permission("treasury.write"))])
def session_match(session_id:int,payload:MatchCreate,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    s=db.get(ReconciliationSession,session_id)
    if not s: raise HTTPException(404,"Reconciliation session not found")
    try:ensure_company(db,payload.company_id,current_user)
    except ValueError as e:fail(e)
    if s.company_id!=payload.company_id: raise HTTPException(403,"Session is outside the company")
    try:o=match(db,s,payload,current_user);db.commit();db.refresh(o);return o
    except ValueError as e:db.rollback();fail(e)

@router.get("/sessions/{session_id}/matches",response_model=list[MatchResponse])
def session_matches(session_id:int,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    s=db.get(ReconciliationSession,session_id)
    if not s: raise HTTPException(404,"Reconciliation session not found")
    ensure_company(db,s.company_id,current_user);return db.scalars(select(ReconciliationMatch).where(ReconciliationMatch.session_id==session_id)).all()

@router.post("/sessions/{session_id}/close",response_model=ReconciliationResponse,dependencies=[Depends(require_permission("treasury.post"))])
def session_close(session_id:int,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    s=db.get(ReconciliationSession,session_id)
    if not s: raise HTTPException(404,"Reconciliation session not found")
    try:ensure_company(db,s.company_id,current_user);o=close_session(db,s,current_user);db.commit();db.refresh(o);return o
    except ValueError as e:db.rollback();fail(e)


@router.delete("/sessions/{session_id}/matches/{match_id}", status_code=204, dependencies=[Depends(require_permission("treasury.write"))])
def session_unmatch(session_id:int, match_id:int, current_user:User=Depends(get_current_user), db:Session=Depends(get_db)):
    s=db.get(ReconciliationSession,session_id)
    if not s: raise HTTPException(404,"Reconciliation session not found")
    try:
        ensure_company(db,s.company_id,current_user); unmatch(db,s,match_id); db.commit()
    except ValueError as e:
        db.rollback(); fail(e)
