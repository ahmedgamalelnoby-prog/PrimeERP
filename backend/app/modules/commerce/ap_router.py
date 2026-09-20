from datetime import date
from fastapi import APIRouter,Depends,HTTPException,Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.companies.models import Company
from app.modules.commerce.ap_models import APWriteOff,APVarianceWorkflow
from app.modules.commerce.ap_schemas import *
from app.modules.commerce.ap_service import ap_service
router=APIRouter(prefix="/ap",tags=["Accounts Payable"],dependencies=[Depends(require_permission("commerce.access"))])
def company(db,cid,u):
 x=db.scalar(select(Company).where(Company.id==cid,Company.tenant_id==u.tenant_id))
 if not x:raise HTTPException(403,"Company is outside the current tenant")
def run(fn):
 try:return fn()
 except HTTPException:raise
 except ValueError as e:raise HTTPException(400,str(e))
@router.post("/advance-payments")
def advance(p:APAdvancePaymentRequest,u:User=Depends(get_current_user),db:Session=Depends(get_db)):
 company(db,p.company_id,u);x=run(lambda:ap_service.create_advance(db,p.company_id,p,u.id));db.commit();return {"payment_id":x.id,"partner_id":x.partner_id,"amount":str(x.amount),"unapplied":str(ap_service.unapplied(db,x))}
@router.post("/payments/{payment_id}/allocate")
def allocate(payment_id:int,p:APAllocateRequest,u=Depends(get_current_user),db:Session=Depends(get_db)):
 if p.payment_id!=payment_id:raise HTTPException(400,"Payment id mismatch")
 company(db,p.company_id,u);x=run(lambda:ap_service.allocate(db,p.company_id,payment_id,p.allocations,u.id));db.commit();return x
@router.post("/payments/{payment_id}/auto-match")
def match(payment_id:int,p:APMatchRequest,u=Depends(get_current_user),db:Session=Depends(get_db)):
 if p.payment_id!=payment_id:raise HTTPException(400,"Payment id mismatch")
 company(db,p.company_id,u);x=run(lambda:ap_service.auto_match(db,p.company_id,payment_id,u.id,p.as_of));db.commit();return x
@router.get("/payments/{payment_id}/unapplied")
def unapplied(payment_id:int,company_id:int=Query(...),u=Depends(get_current_user),db:Session=Depends(get_db)):
 company(db,company_id,u);p=ap_service._payment(db,company_id,payment_id);return {"payment_id":p.id,"unapplied":str(ap_service.unapplied(db,p))}
@router.post("/write-offs")
def wo(p:APWriteOffRequest,u=Depends(get_current_user),db:Session=Depends(get_db)):
 company(db,p.company_id,u);x=run(lambda:ap_service.request_writeoff(db,p.company_id,p,u.id));db.commit();return x
@router.post("/variances")
def variance(p:APVarianceCreateRequest,u=Depends(get_current_user),db:Session=Depends(get_db)):
 company(db,p.company_id,u);x=run(lambda:ap_service.create_variance(db,p.company_id,p,u.id));db.commit();return x
@router.post("/variances/{variance_id}/decision")
def variance_decision(variance_id:int,p:APVarianceDecision,u=Depends(get_current_user),db:Session=Depends(get_db)):
 company(db,p.company_id,u);x=run(lambda:ap_service.decide_variance(db,p.company_id,variance_id,p,u));db.commit();return x
@router.get("/variances")
def variances(company_id:int=Query(...),status:str|None=None,u=Depends(get_current_user),db:Session=Depends(get_db)):
 company(db,company_id,u);q=select(APVarianceWorkflow).where(APVarianceWorkflow.company_id==company_id)
 if status:q=q.where(APVarianceWorkflow.status==status)
 return list(db.scalars(q.order_by(APVarianceWorkflow.id.desc()).limit(500)).all())
@router.post("/reconcile")
def reconcile(p:APReconcileRequest,u=Depends(get_current_user),db:Session=Depends(get_db)):
 company(db,p.company_id,u);x=run(lambda:ap_service.reconcile(db,p.company_id,p.partner_id,p.as_of or date.today(),u.id,p.persist));db.commit();return x
