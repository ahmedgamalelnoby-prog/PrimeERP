from datetime import datetime
from decimal import Decimal
import hashlib
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.modules.commerce.models import CommercePayment
from app.modules.treasury.models import Cheque
from .models import BankAccount, BankStatement, BankStatementLine, ReconciliationSession, ReconciliationMatch

def fingerprint_line(payload) -> str:
    raw = "|".join(str(getattr(payload, k, "") or "") for k in ("external_id","transaction_date","value_date","reference","cheque_number","debit","credit","currency","description"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def ensure_company(db, company_id, user):
    from app.modules.companies.models import Company
    if user.tenant_id is None: raise ValueError("User is not assigned to a tenant")
    if db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == user.tenant_id)) is None:
        raise ValueError("Company is outside the current tenant")

def create_account(db, payload, user):
    ensure_company(db,payload.company_id,user)
    obj=BankAccount(**payload.model_dump())
    db.add(obj); db.flush(); return obj

def create_statement(db, payload, user):
    ensure_company(db,payload.company_id,user)
    account=db.scalar(select(BankAccount).where(BankAccount.id==payload.bank_account_id,BankAccount.company_id==payload.company_id))
    if not account: raise ValueError("Bank account not found")
    if payload.period_end < payload.period_start: raise ValueError("Statement period is invalid")
    obj=BankStatement(**payload.model_dump()); db.add(obj); db.flush(); return obj

def add_line(db, statement, payload):
    if statement.status=="closed": raise ValueError("Closed statement is immutable")
    if payload.debit>0 and payload.credit>0: raise ValueError("Statement line cannot have both debit and credit")
    if payload.debit==0 and payload.credit==0: raise ValueError("Statement line must have a debit or credit amount")
    obj=BankStatementLine(statement_id=statement.id,company_id=statement.company_id,fingerprint=fingerprint_line(payload),**payload.model_dump())
    existing=db.scalar(select(BankStatementLine).where(BankStatementLine.statement_id==statement.id,BankStatementLine.fingerprint==obj.fingerprint))
    if existing: return existing, False
    db.add(obj); db.flush(); return obj, True

def create_session(db,payload,user):
    ensure_company(db,payload.company_id,user)
    st=db.scalar(select(BankStatement).where(BankStatement.id==payload.statement_id,BankStatement.company_id==payload.company_id,BankStatement.bank_account_id==payload.bank_account_id))
    if not st: raise ValueError("Statement not found")
    if st.status=="closed": raise ValueError("Statement is already closed")
    existing=db.scalar(select(ReconciliationSession).where(ReconciliationSession.statement_id==st.id))
    if existing: return existing
    obj=ReconciliationSession(company_id=payload.company_id,bank_account_id=payload.bank_account_id,statement_id=st.id,book_balance=payload.book_balance,bank_balance=st.closing_balance,difference=payload.book_balance-st.closing_balance)
    obj.status="balanced" if obj.difference==0 else "open"
    db.add(obj); db.flush(); return obj

def _line(db, session, line_id):
    line=db.scalar(select(BankStatementLine).where(BankStatementLine.id==line_id,BankStatementLine.company_id==session.company_id,BankStatementLine.statement_id==session.statement_id))
    if not line: raise ValueError("Statement line not found")
    return line

def match(db, session, payload, user):
    if session.status=="closed": raise ValueError("Closed reconciliation is immutable")
    line=_line(db,session,payload.statement_line_id)
    if payload.amount > (line.debit if line.debit else line.credit) - line.matched_amount: raise ValueError("Match amount exceeds the unmatched statement amount")
    if payload.source_type=="payment":
        source=db.scalar(select(CommercePayment).where(CommercePayment.id==payload.source_id,CommercePayment.company_id==session.company_id,CommercePayment.status=="posted"))
    else:
        source=db.scalar(select(Cheque).where(Cheque.id==payload.source_id,Cheque.company_id==session.company_id))
    if not source: raise ValueError("Source transaction not found")
    if payload.source_type=="payment":
        if payload.amount > source.amount: raise ValueError("Match exceeds payment amount")
        expected_side = "credit" if source.document_kind == "sale" else "debit"
    else:
        if payload.amount > source.amount: raise ValueError("Match exceeds cheque amount")
        expected_side = "credit" if source.direction == "received" else "debit"
    if expected_side == "credit" and line.credit <= 0: raise ValueError("Received/sales sources can only match bank credits")
    if expected_side == "debit" and line.debit <= 0: raise ValueError("Issued/purchase sources can only match bank debits")
    existing=db.scalar(select(ReconciliationMatch).where(ReconciliationMatch.statement_line_id==line.id,ReconciliationMatch.source_type==payload.source_type,ReconciliationMatch.source_id==payload.source_id))
    if existing: raise ValueError("Source transaction is already matched to this statement line")
    obj=ReconciliationMatch(company_id=session.company_id,session_id=session.id,statement_line_id=line.id,source_type=payload.source_type,source_id=payload.source_id,amount=payload.amount,created_by=user.id)
    db.add(obj); line.matched_amount += payload.amount
    total=(line.debit if line.debit else line.credit)
    line.status="matched" if line.matched_amount==total else "partial"
    db.flush(); return obj

def auto_match(db,session,user):
    lines=db.scalars(select(BankStatementLine).where(BankStatementLine.company_id==session.company_id,BankStatementLine.statement_id==session.statement_id,BankStatementLine.status!="matched")).all()
    matched=0; candidates=0
    for line in lines:
        amount=line.debit if line.debit else line.credit
        if amount <= line.matched_amount: continue
        q=select(CommercePayment).where(CommercePayment.company_id==session.company_id,CommercePayment.status=="posted",CommercePayment.amount==amount)
        if line.reference: q=q.where(CommercePayment.reference==line.reference)
        candidates_list=db.scalars(q.limit(2)).all()
        candidates += len(candidates_list)
        if len(candidates_list)==1:
            try:
                match(db,session,type("P",(),{"statement_line_id":line.id,"source_type":"payment","source_id":candidates_list[0].id,"amount":amount})(),user); matched+=1
            except ValueError: pass
            continue
        cq=select(Cheque).where(Cheque.company_id==session.company_id,Cheque.amount==amount)
        if line.cheque_number: cq=cq.where(Cheque.cheque_number==line.cheque_number)
        cs=db.scalars(cq.limit(2)).all(); candidates += len(cs)
        if len(cs)==1:
            try:
                match(db,session,type("P",(),{"statement_line_id":line.id,"source_type":"cheque","source_id":cs[0].id,"amount":amount})(),user); matched+=1
            except ValueError: pass
    return matched,candidates

def refresh_session(session, db=None):
    session.difference=session.book_balance-session.bank_balance
    if session.status!="closed":
        unmatched = 0
        if db is not None:
            unmatched = db.scalar(select(func.count(BankStatementLine.id)).where(
                BankStatementLine.statement_id==session.statement_id,
                BankStatementLine.status!="matched",
            )) or 0
        session.status="balanced" if session.difference==0 and unmatched==0 else "open"

def close_session(db,session,user):
    refresh_session(session, db)
    if session.status!="balanced": raise ValueError("Reconciliation can only be closed when balanced and all statement lines are matched")
    session.status="closed"; session.closed_by=user.id; session.closed_at=datetime.utcnow()
    st=db.get(BankStatement,session.statement_id); st.status="closed"
    db.flush(); return session


def unmatch(db, session, match_id):
    if session.status=="closed": raise ValueError("Closed reconciliation is immutable")
    obj=db.scalar(select(ReconciliationMatch).where(ReconciliationMatch.id==match_id,ReconciliationMatch.session_id==session.id,ReconciliationMatch.company_id==session.company_id))
    if not obj: raise ValueError("Reconciliation match not found")
    line=db.get(BankStatementLine,obj.statement_line_id)
    line.matched_amount -= obj.amount
    total=(line.debit if line.debit else line.credit)
    line.status="matched" if line.matched_amount==total else ("partial" if line.matched_amount>0 else "unmatched")
    db.delete(obj); db.flush()
