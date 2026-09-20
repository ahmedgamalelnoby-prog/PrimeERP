from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.companies.models import Company
from app.modules.commerce.ar_schemas import ARAutoMatchRequest, ARAllocateRequest, ARWriteOffRequest, ARWriteOffDecision, ARReconcileRequest, ARAdvanceReceiptRequest
from app.modules.commerce.ar_models import ARWriteOff
from app.modules.commerce.ar_service import ar_service

router=APIRouter(prefix="/ar",tags=["Accounts Receivable"],dependencies=[Depends(require_permission("commerce.access"))])

def company(db,company_id,user):
    if user.tenant_id is None: raise HTTPException(403,"Tenant context required")
    obj=db.scalar(select(Company).where(Company.id==company_id,Company.tenant_id==user.tenant_id))
    if obj is None: raise HTTPException(403,"Company is outside the current tenant")
    return obj

def run(fn):
    try:return fn()
    except HTTPException:raise
    except ValueError as e:raise HTTPException(400,str(e)) from e

@router.post("/advance-receipts",dependencies=[Depends(require_permission("commerce.payment"))])
def advance_receipt(payload:ARAdvanceReceiptRequest,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    company(db,payload.company_id,current_user)
    obj=run(lambda:ar_service.create_advance(db,payload.company_id,payload,current_user.id));db.commit();db.refresh(obj)
    return {"payment_id":obj.id,"partner_id":obj.partner_id,"amount":str(obj.amount),"unapplied":str(ar_service.unapplied(db,obj)),"status":obj.status}

@router.post("/payments/{payment_id}/allocate",dependencies=[Depends(require_permission("commerce.payment"))])
def allocate(payment_id:int,payload:ARAllocateRequest,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    if payload.payment_id!=payment_id:raise HTTPException(400,"Payment id mismatch")
    company(db,payload.company_id,current_user); result=run(lambda:ar_service.allocate(db,payload.company_id,payment_id,payload.allocations,current_user.id));db.commit();return result

@router.post("/payments/{payment_id}/auto-match",dependencies=[Depends(require_permission("commerce.payment"))])
def auto_match(payment_id:int,payload:ARAutoMatchRequest,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    if payload.payment_id!=payment_id:raise HTTPException(400,"Payment id mismatch")
    company(db,payload.company_id,current_user);result=run(lambda:ar_service.auto_match(db,payload.company_id,payment_id,current_user.id,payload.as_of));db.commit();return result

@router.post("/payments/{payment_id}/reverse",dependencies=[Depends(require_permission("commerce.reverse"))])
def reverse_advance(payment_id:int,payload:ARAdvanceReceiptRequest,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    company(db,payload.company_id,current_user)
    from app.modules.commerce.service import commerce_service
    obj=run(lambda:commerce_service.reverse_payment(db,payload.company_id,payment_id,payload.payment_date,payload.notes,current_user.id));db.commit()
    return {"payment_id":payment_id,"status":"reversed","reversal_date":payload.payment_date}

@router.get("/payments/{payment_id}/unapplied")
def unapplied(payment_id:int,company_id:int=Query(...,gt=0),current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    company(db,company_id,current_user);p=ar_service._payment(db,company_id,payment_id);return {"payment_id":p.id,"amount":str(p.amount),"allocated":str(Decimal(str(p.amount))-ar_service.unapplied(db,p)),"unapplied":str(ar_service.unapplied(db,p))}

@router.post("/write-offs",dependencies=[Depends(require_permission("commerce.write"))])
def writeoff(payload:ARWriteOffRequest,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    company(db,payload.company_id,current_user);obj=run(lambda:ar_service.request_writeoff(db,payload.company_id,payload,current_user.id));db.commit();db.refresh(obj);return obj

@router.post("/write-offs/{writeoff_id}/decision",dependencies=[Depends(require_permission("commerce.post"))])
def writeoff_decision(writeoff_id:int,payload:ARWriteOffDecision,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    company(db,payload.company_id,current_user);obj=run(lambda:ar_service.decide_writeoff(db,payload.company_id,writeoff_id,payload,current_user));db.commit();db.refresh(obj);return obj

@router.get("/write-offs")
def writeoffs(company_id:int=Query(...,gt=0),status:str|None=None,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    company(db,company_id,current_user);q=select(ARWriteOff).where(ARWriteOff.company_id==company_id)
    if status:q=q.where(ARWriteOff.status==status)
    return list(db.scalars(q.order_by(ARWriteOff.id.desc()).limit(500)).all())

@router.post("/reconcile",dependencies=[Depends(require_permission("commerce.write"))])
def reconcile(payload:ARReconcileRequest,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    company(db,payload.company_id,current_user);result=run(lambda:ar_service.reconcile(db,payload.company_id,payload.partner_id,payload.as_of or date.today(),current_user.id,payload.persist));db.commit();return result

@router.get("/credit/{partner_id}")
def credit(partner_id:int,company_id:int=Query(...,gt=0),current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    company(db,company_id,current_user);p=ar_service._partner(db,company_id,partner_id);from app.modules.commerce.service import commerce_service
    exposure=commerce_service.partner_open_balance(db,company_id,partner_id,"customer")
    return {"partner_id":partner_id,"credit_limit":str(p.credit_limit or 0),"current_exposure":str(exposure),"available_credit":str(max(Decimal(p.credit_limit or 0)-exposure,Decimal(0))) if Decimal(p.credit_limit or 0)>0 else None}
