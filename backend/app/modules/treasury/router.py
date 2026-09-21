from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.companies.models import Company
from app.modules.branches.models import Branch
from app.modules.accounting.chart_of_accounts.models import AccountCombination
from app.modules.accounting.journals.schemas.journal import JournalEntryCreate, JournalLineCreate
from app.modules.accounting.journals.services.journal_service import journal_service
from app.modules.transactions.services.numbering_service import numbering_service
from .models import TreasuryAccount,TreasuryTransaction,TreasuryTransfer,Cheque,PaymentAllocation
from .schemas import TreasuryAccountCreate,TreasuryTransactionCreate,TransferCreate,ChequeCreate,AllocationCreate,ChequeStatusChange,TreasuryPosting
router=APIRouter()
def tenant(u):
    if u.is_platform_admin or u.tenant_id is None: raise HTTPException(403,"An active tenant context is required")
    return u.tenant_id
def account(db,t,i):
    x=db.scalar(select(TreasuryAccount).where(TreasuryAccount.id==i,TreasuryAccount.tenant_id==t,TreasuryAccount.is_active.is_(True)))
    if not x: raise HTTPException(404,"Treasury account not found")
    return x
@router.get("/accounts")
def accounts(db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return list(db.scalars(select(TreasuryAccount).where(TreasuryAccount.tenant_id==tenant(current_user)).order_by(TreasuryAccount.code)).all())
@router.post("/accounts",status_code=201)
def create_account(p:TreasuryAccountCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    t=tenant(current_user)
    if not db.scalar(select(Company).where(Company.id==p.company_id,Company.tenant_id==t)): raise HTTPException(404,"Company not found")
    if not db.scalar(select(Branch).where(Branch.id==p.branch_id,Branch.company_id==p.company_id,Branch.tenant_id==t)): raise HTTPException(404,"Branch not found for company")
    x=TreasuryAccount(tenant_id=t,**p.model_dump()); db.add(x); db.commit(); db.refresh(x); return x
@router.post("/transactions",status_code=201)
def transaction(p:TreasuryTransactionCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    t=tenant(current_user); a=account(db,t,p.treasury_account_id)
    if p.direction not in ("in","out"): raise HTTPException(422,"direction must be in or out")
    seq=numbering_service.generate_next_number(db,t,a.company_id,a.branch_id,"TREASURY_TX",commit=False)
    x=TreasuryTransaction(tenant_id=t,transaction_number=seq["generated_number"],created_by=current_user.id,**p.model_dump()); db.add(x); db.commit(); db.refresh(x); return x
@router.post("/transactions/{transaction_id}/post",status_code=200)
def post_transaction(transaction_id:int,p:TreasuryPosting,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    t=tenant(current_user); tx=db.scalar(select(TreasuryTransaction).where(TreasuryTransaction.id==transaction_id,TreasuryTransaction.tenant_id==t))
    if not tx: raise HTTPException(404,"Treasury transaction not found")
    if tx.status=="reversed": raise HTTPException(409,"Reversed transaction cannot be posted")
    if tx.journal_entry_id: return tx
    a=account(db,t,tx.treasury_account_id)
    if not a.accounting_account_combination_id: raise HTTPException(422,"Treasury account is not linked to an accounting account")
    offset=db.scalar(select(AccountCombination).where(AccountCombination.id==p.offset_account_combination_id,AccountCombination.company_id==a.company_id,AccountCombination.is_active.is_(True)))
    if not offset: raise HTTPException(404,"Offset account not found for company")
    lines=[JournalLineCreate(account_combination_id=a.accounting_account_combination_id,debit=tx.amount if tx.direction=="in" else 0,credit=tx.amount if tx.direction=="out" else 0),JournalLineCreate(account_combination_id=offset.id,debit=tx.amount if tx.direction=="out" else 0,credit=tx.amount if tx.direction=="in" else 0)]
    je=journal_service.create_entry(db,JournalEntryCreate(company_id=a.company_id,branch_id=a.branch_id,journal_id=p.journal_id,fiscal_year_id=p.fiscal_year_id,period_id=p.period_id,entry_date=tx.transaction_date,description=tx.description or f"Treasury transaction {tx.transaction_number}",lines=lines,source_module="treasury",source_entity="treasury_transaction",source_id=tx.id),current_user)
    tx.journal_entry_id=je.id; tx.status="posted"; db.commit(); db.refresh(tx); return tx

@router.post("/cheques/{cheque_id}/status")
def cheque_status(cheque_id:int,p:ChequeStatusChange,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    t=tenant(current_user); x=db.scalar(select(Cheque).where(Cheque.id==cheque_id,Cheque.tenant_id==t))
    if not x: raise HTTPException(404,"Cheque not found")
    allowed={"received":{"deposited","returned"},"deposited":{"cleared","bounced","returned"},"cleared":set(),"bounced":{"deposited","returned"},"returned":set()}
    if p.status not in allowed.get(x.status,set()): raise HTTPException(409,f"Invalid cheque transition {x.status}->{p.status}")
    x.status=p.status; db.commit(); db.refresh(x); return x

@router.post("/transfers",status_code=201)
def transfer(p:TransferCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    t=tenant(current_user); a=account(db,t,p.from_account_id); b=account(db,t,p.to_account_id)
    if a.id==b.id: raise HTTPException(422,"Transfer accounts must differ")
    seq=numbering_service.generate_next_number(db,t,a.company_id,a.branch_id,"TREASURY_TRANSFER",commit=False)
    x=TreasuryTransfer(tenant_id=t,transfer_number=seq["generated_number"],created_by=current_user.id,**p.model_dump()); db.add(x); db.commit(); db.refresh(x); return x
@router.post("/cheques",status_code=201)
def cheque(p:ChequeCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    t=tenant(current_user); account(db,t,p.treasury_account_id); x=Cheque(tenant_id=t,**p.model_dump()); db.add(x); db.commit(); db.refresh(x); return x
@router.post("/allocations",status_code=201)
def allocation(p:AllocationCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    t=tenant(current_user); tx=db.scalar(select(TreasuryTransaction).where(TreasuryTransaction.id==p.treasury_transaction_id,TreasuryTransaction.tenant_id==t))
    if not tx: raise HTTPException(404,"Treasury transaction not found")
    used=sum((x.amount for x in db.scalars(select(PaymentAllocation).where(PaymentAllocation.treasury_transaction_id==tx.id)).all()),0)
    if used+p.amount>tx.amount: raise HTTPException(409,"Allocation exceeds transaction amount")
    x=PaymentAllocation(tenant_id=t,**p.model_dump()); db.add(x); db.commit(); db.refresh(x); return x
