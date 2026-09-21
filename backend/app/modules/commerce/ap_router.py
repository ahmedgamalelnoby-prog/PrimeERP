from datetime import date
from decimal import Decimal
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
from app.modules.commerce.ap_completion_service import ap_completion_service
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
@router.post("/write-offs/{writeoff_id}/decision")
def writeoff_decision(writeoff_id:int,p:APWriteOffDecision,u=Depends(get_current_user),db:Session=Depends(get_db)):
 company(db,p.company_id,u);x=run(lambda:ap_completion_service.decide_writeoff(db,p.company_id,writeoff_id,p.approve,p.reason,u.id));db.commit();return x
@router.post("/write-offs")
def wo(p:APWriteOffRequest,u=Depends(get_current_user),db:Session=Depends(get_db)):
 company(db,p.company_id,u);x=run(lambda:ap_service.request_writeoff(db,p.company_id,p,u.id));db.commit();return x
@router.get("/three-way-match/{bill_id}")
def three_way(bill_id:int,company_id:int=Query(...),tolerance:float=0,u=Depends(get_current_user),db:Session=Depends(get_db)):
 company(db,company_id,u);return run(lambda:ap_completion_service.apply_variance(db,company_id,bill_id,u.id,Decimal(str(tolerance))))
@router.post("/variances")
def variance(p:APVarianceCreateRequest,u=Depends(get_current_user),db:Session=Depends(get_db)):
 company(db,p.company_id,u);x=run(lambda:ap_service.create_variance(db,p.company_id,p,u.id));db.commit();return x
@router.post("/variances/{variance_id}/decision")
def variance_decision(variance_id:int,p:APVarianceDecision,u=Depends(get_current_user),db:Session=Depends(get_db)):
 company(db,p.company_id,u);x=run(lambda:ap_completion_service.decide_variance(db,p.company_id,variance_id,p.approve,p.reason,u.id,p.waive));db.commit();return x
@router.get("/variances")
def variances(company_id:int=Query(...),status:str|None=None,u=Depends(get_current_user),db:Session=Depends(get_db)):
 company(db,company_id,u);q=select(APVarianceWorkflow).where(APVarianceWorkflow.company_id==company_id)
 if status:q=q.where(APVarianceWorkflow.status==status)
 return list(db.scalars(q.order_by(APVarianceWorkflow.id.desc()).limit(500)).all())
@router.get("/suppliers/{partner_id}/aging")
def supplier_aging(partner_id:int,company_id:int=Query(...),as_of:date|None=None,u=Depends(get_current_user),db:Session=Depends(get_db)):
 company(db,company_id,u);return ap_completion_service.supplier_aging(db,company_id,partner_id,as_of or date.today())
@router.get("/suppliers/{partner_id}/statement")
def supplier_statement(partner_id:int,company_id:int=Query(...),from_date:date|None=None,to_date:date|None=None,as_of:date|None=None,u=Depends(get_current_user),db:Session=Depends(get_db)):
 company(db,company_id,u);return run(lambda:ap_completion_service.supplier_statement(db,company_id,partner_id,from_date,to_date,as_of or to_date or date.today()))
@router.post("/reconcile")
def reconcile(p:APReconcileRequest,u=Depends(get_current_user),db:Session=Depends(get_db)):
 company(db,p.company_id,u);x=run(lambda:ap_completion_service.reconcile(db,p.company_id,p.partner_id,p.as_of or date.today(),u.id,p.persist));db.commit();return x
