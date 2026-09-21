from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.companies.models import Company
from app.modules.branches.models import Branch
from app.modules.transactions.services.numbering_service import numbering_service
from .models import TreasuryAccount,TreasuryTransaction,TreasuryTransfer,Cheque,PaymentAllocation
from .schemas import TreasuryAccountCreate,TreasuryTransactionCreate,TransferCreate,ChequeCreate,AllocationCreate
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
