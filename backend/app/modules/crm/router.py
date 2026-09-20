from datetime import datetime,date
from decimal import Decimal
from fastapi import APIRouter,Depends,HTTPException,Query
from pydantic import BaseModel,Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from .models import CRMLead
from app.modules.completion.domain_models import CRMOpportunity,CRMActivity
router=APIRouter(prefix="/crm",tags=["CRM"])
def scope(db,user,company_id):
    if user.tenant_id is None or db.scalar(select(Company).where(Company.id==company_id,Company.tenant_id==user.tenant_id)) is None: raise HTTPException(403,"Company is outside the current tenant")
class LeadIn(BaseModel):
    name:str=Field(min_length=1,max_length=200); phone:str|None=None; email:str|None=None; source:str|None=None; owner_id:int|None=None; notes:str|None=None
class OppIn(BaseModel):
    name:str=Field(min_length=1,max_length=200); lead_id:int|None=None; amount:Decimal=Field(default=0,ge=0); probability:Decimal=Field(default=0,ge=0,le=100); expected_close:date|None=None; owner_id:int|None=None; notes:str|None=None
class StageIn(BaseModel):
    stage:str=Field(pattern="^(qualification|proposal|negotiation|won|lost)$"); lost_reason:str|None=None
class ActivityIn(BaseModel):
    activity_type:str=Field(pattern="^(call|meeting|email|task|followup)$"); subject:str=Field(min_length=1,max_length=255); due_at:datetime|None=None; assigned_to:int|None=None; notes:str|None=None
@router.post("/leads",status_code=201)
def create_lead(p:LeadIn,company_id:int=Query(...,gt=0),user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    scope(db,user,company_id); o=CRMLead(company_id=company_id,**p.model_dump()); db.add(o); db.commit(); db.refresh(o); return o
@router.get("/leads")
def list_leads(company_id:int=Query(...,gt=0),status:str|None=None,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    scope(db,user,company_id); q=select(CRMLead).where(CRMLead.company_id==company_id)
    if status:q=q.where(CRMLead.status==status)
    return list(db.scalars(q.order_by(CRMLead.id.desc())).all())
@router.patch("/leads/{lead_id}/status")
def lead_status(lead_id:int,status:str=Query(...,pattern="^(new|qualified|converted|lost)$"),company_id:int=Query(...,gt=0),user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    scope(db,user,company_id); o=db.scalar(select(CRMLead).where(CRMLead.id==lead_id,CRMLead.company_id==company_id))
    if not o:raise HTTPException(404,"Lead not found")
    o.status=status;db.commit();return o
@router.post("/opportunities",status_code=201)
def create_opportunity(p:OppIn,company_id:int=Query(...,gt=0),user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    scope(db,user,company_id)
    if p.lead_id is not None and not db.scalar(select(CRMLead.id).where(CRMLead.id==p.lead_id,CRMLead.company_id==company_id)):
        raise HTTPException(422,"Lead does not belong to the company")
    o=CRMOpportunity(company_id=company_id,code=p.name,amount=p.amount,value=p.amount,probability=p.probability,expected_close=p.expected_close,owner_id=p.owner_id,lead_id=p.lead_id,notes=p.notes);db.add(o);db.commit();db.refresh(o);return o
@router.get("/opportunities")
def opportunities(company_id:int=Query(...,gt=0),stage:str|None=None,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    scope(db,user,company_id);q=select(CRMOpportunity).where(CRMOpportunity.company_id==company_id)
    if stage:q=q.where(CRMOpportunity.stage==stage)
    return list(db.scalars(q.order_by(CRMOpportunity.id.desc())).all())
@router.post("/opportunities/{opportunity_id}/stage")
def opportunity_stage(opportunity_id:int,p:StageIn,company_id:int=Query(...,gt=0),user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    scope(db,user,company_id);o=db.scalar(select(CRMOpportunity).where(CRMOpportunity.id==opportunity_id,CRMOpportunity.company_id==company_id).with_for_update())
    if not o:raise HTTPException(404,"Opportunity not found")
    if p.stage=="lost" and not p.lost_reason:raise HTTPException(422,"Lost reason is required")
    o.stage=p.stage;o.status="won" if p.stage=="won" else ("lost" if p.stage=="lost" else "open");o.lost_reason=p.lost_reason;db.commit();return o
@router.post("/opportunities/{opportunity_id}/activities",status_code=201)
def activity(opportunity_id:int,p:ActivityIn,company_id:int=Query(...,gt=0),user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    scope(db,user,company_id)
    if not db.scalar(select(CRMOpportunity.id).where(CRMOpportunity.id==opportunity_id,CRMOpportunity.company_id==company_id)):raise HTTPException(404,"Opportunity not found")
    o=CRMActivity(company_id=company_id,opportunity_id=opportunity_id,user_id=p.assigned_to,activity_type=p.activity_type,subject=p.subject,due_at=p.due_at,notes=p.notes);db.add(o);db.commit();db.refresh(o);return o
@router.post("/activities/{activity_id}/complete")
def complete_activity(activity_id:int,company_id:int=Query(...,gt=0),user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    scope(db,user,company_id);o=db.scalar(select(CRMActivity).where(CRMActivity.id==activity_id,CRMActivity.company_id==company_id).with_for_update())
    if not o:raise HTTPException(404,"Activity not found")
    o.status="completed";o.completed_at=datetime.utcnow();db.commit();return o
@router.get("/dashboard")
def dashboard(company_id:int=Query(...,gt=0),user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    scope(db,user,company_id); rows=db.scalars(select(CRMOpportunity).where(CRMOpportunity.company_id==company_id)).all()
    weighted=sum((Decimal(x.value or 0)*Decimal(x.probability or 0)/100 for x in rows),Decimal(0))
    return {"opportunities":len(rows),"open_amount":sum((Decimal(x.amount or 0) for x in rows if x.status=="open"),Decimal(0)),"weighted_pipeline":weighted,"won_amount":sum((Decimal(x.amount or 0) for x in rows if x.status=="won"),Decimal(0))}
