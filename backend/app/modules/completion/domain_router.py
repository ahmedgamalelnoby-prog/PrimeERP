from datetime import date, datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from .domain_service import domain_completion_service
from .domain_models import *

router=APIRouter(prefix="/completion/domains",tags=["Domain Completion"])

def company(db,cid,u): return domain_completion_service._tenant(db,cid,u)

@router.post("/aging")
def aging(p:dict,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    company(db,int(p["company_id"]),u); p=dict(p); p.pop("tenant_id",None); return domain_completion_service.save_aging(db,u.tenant_id,int(p["company_id"]),int(p["partner_id"]),str(p["direction"]),date.fromisoformat(p["as_of_date"]))

@router.post("/writeoffs")
def writeoff(p:dict,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    company(db,int(p["company_id"]),u)
    x=domain_completion_service.writeoff(db,tenant_id=u.tenant_id,**p);db.commit();db.refresh(x);return x

@router.post("/writeoffs/{id}/approve")
def approve(id:int,company_id:int=Query(...),db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    company(db,company_id,u);x=db.scalar(select(FinanceWriteOff).where(FinanceWriteOff.id==id,FinanceWriteOff.company_id==company_id).with_for_update())
    if not x: raise HTTPException(404,"Write-off not found")
    x=domain_completion_service.approve_writeoff(db,x,u.id);db.commit();db.refresh(x);return x

@router.post("/writeoffs/{id}/post")
def post_writeoff(id:int,company_id:int=Query(...),db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    company(db,company_id,u);x=db.scalar(select(FinanceWriteOff).where(FinanceWriteOff.id==id,FinanceWriteOff.company_id==company_id).with_for_update())
    if not x: raise HTTPException(404,"Write-off not found")
    x=domain_completion_service.post_writeoff(db,x,u.id);db.commit();db.refresh(x);return x

@router.post("/reconcile")
def reconcile(p:dict,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    company(db,int(p["company_id"]),u); p=dict(p); p.pop("tenant_id",None); x=domain_completion_service.reconcile(db,tenant_id=u.tenant_id,**p);db.commit();db.refresh(x);return x

@router.post("/inventory/trace")
def trace(p:dict,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    company(db,int(p["company_id"]),u);x=domain_completion_service.trace(db,**p);db.commit();db.refresh(x);return x

@router.post("/manufacturing/work-orders")
def work_order(p:dict,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    company(db,int(p["company_id"]),u);x=domain_completion_service.work_order(db,**p);db.commit();db.refresh(x);return x

@router.patch("/manufacturing/work-orders/{id}/status")
def work_status(id:int,status:str=Query(...),company_id:int=Query(...),db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    company(db,company_id,u);x=db.scalar(select(ManufacturingWorkOrder).where(ManufacturingWorkOrder.id==id,ManufacturingWorkOrder.company_id==company_id).with_for_update())
    if not x: raise HTTPException(404,"Work order not found")
    x=domain_completion_service.work_order_status(db,x,status);db.commit();db.refresh(x);return x

@router.post("/crm/opportunities")
def opportunity(p:dict,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    company(db,int(p["company_id"]),u);x=domain_completion_service.crm_opportunity(db,**p);db.commit();db.refresh(x);return x

@router.post("/crm/activities")
def activity(p:dict,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    company(db,int(p["company_id"]),u);x=CRMActivity(**p);db.add(x);db.commit();db.refresh(x);return x

@router.post("/hr/attendance")
def attendance(p:dict,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    company(db,int(p["company_id"]),u); p=dict(p); p.pop("tenant_id",None); x=HRAttendance(**p,tenant_id=u.tenant_id);db.add(x);db.commit();db.refresh(x);return x

@router.post("/hr/leaves")
def leave(p:dict,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    company(db,int(p["company_id"]),u); p=dict(p); p.pop("tenant_id",None); x=HRLeave(**p,tenant_id=u.tenant_id);db.add(x);db.commit();db.refresh(x);return x

@router.post("/hr/leaves/{id}/decision")
def leave_decision(id:int,status:str=Query(...,pattern="^(approved|rejected|cancelled)$"),company_id:int=Query(...),db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    company(db,company_id,u);x=db.scalar(select(HRLeave).where(HRLeave.id==id,HRLeave.company_id==company_id).with_for_update())
    if not x: raise HTTPException(404,"Leave request not found")
    if x.status!="requested": raise HTTPException(409,"Only requested leave can be decided")
    x.status=status;x.approved_by=u.id if status=="approved" else None;db.commit();db.refresh(x);return x

@router.post("/hr/payroll/runs")
def payroll_run(p:dict,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    company(db,int(p["company_id"]),u); p=dict(p); p.pop("tenant_id",None); x=HRPayrollCompletionRun(tenant_id=u.tenant_id,**p);db.add(x);db.commit();db.refresh(x);return x

@router.post("/tax/filings")
def tax_filing(p:dict,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    company(db,int(p["company_id"]),u);p=dict(p);p.pop("tenant_id",None);p["payable_tax"]=Decimal(str(p.get("output_tax",0)))-Decimal(str(p.get("input_tax",0)))+Decimal(str(p.get("withholding_tax",0)));x=TaxFilingControl(tenant_id=u.tenant_id,**p);db.add(x);db.commit();db.refresh(x);return x

@router.post("/saas/subscriptions/{subscription_id}/lifecycle")
def lifecycle(subscription_id:int,to_status:str=Query(...),reason:str|None=Query(None),db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    x=domain_completion_service.lifecycle(db,subscription_id,to_status,u.id,reason); 
    if x.tenant_id!=u.tenant_id and not u.is_platform_admin: raise HTTPException(403,"Tenant mismatch")
    db.commit();db.refresh(x);return x

@router.post("/developer/api-keys")
def api_key(p:dict,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    if u.tenant_id is None: raise HTTPException(403,"Tenant required")
    if int(p["tenant_id"])!=u.tenant_id and not u.is_platform_admin: raise HTTPException(403,"Tenant mismatch")
    x,raw=domain_completion_service.api_key(db,u.tenant_id,p.get("company_id"),p["name"],p.get("scopes",[]),datetime.fromisoformat(p["expires_at"]) if p.get("expires_at") else None);db.commit();return {"id":x.id,"key":raw,"prefix":x.key_prefix,"expires_at":x.expires_at}

@router.post("/mobile/sync")
def mobile_sync(p:dict,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    company(db,int(p["company_id"]),u); p=dict(p); p.pop("tenant_id",None); x=domain_completion_service.mobile_enqueue(db,tenant_id=u.tenant_id,**p);db.commit();db.refresh(x);return x

@router.post("/workflow")
def workflow(p:dict,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    company(db,int(p["company_id"]),u); p=dict(p); p.pop("tenant_id",None); x=domain_completion_service.workflow(db,tenant_id=u.tenant_id,**p);db.commit();db.refresh(x);return x

@router.post("/workflow/{workflow_id}/steps/{step_id}/decision")
def workflow_decision(workflow_id:int,step_id:int,status:str=Query(...),reason:str|None=Query(None),company_id:int=Query(...),db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    company(db,company_id,u);x=db.scalar(select(WorkflowApprovalStep).where(WorkflowApprovalStep.id==step_id,WorkflowApprovalStep.workflow_id==workflow_id).with_for_update())
    if not x: raise HTTPException(404,"Workflow step not found")
    x=domain_completion_service.workflow_decide(db,x,status,reason);db.commit();db.refresh(x);return x


class WorkflowRulePayload(__import__("pydantic").BaseModel):
    tenant_id:int|None=None
    company_id:int
    module:str
    document_type:str
    condition_json:dict={}
    approval_levels:int=__import__("pydantic").Field(default=1,ge=1,le=20)
    delegation_allowed:bool=False
    escalation_minutes:int|None=__import__("pydantic").Field(default=None,gt=0)

@router.post("/workflow-rules",status_code=201)
def create_workflow_rule(p:WorkflowRulePayload,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    company(db,p.company_id,u)
    x=WorkflowRule(tenant_id=u.tenant_id,company_id=p.company_id,module=p.module,document_type=p.document_type,condition_json=p.condition_json,approval_levels=p.approval_levels,delegation_allowed=p.delegation_allowed,escalation_minutes=p.escalation_minutes)
    db.add(x);db.commit();db.refresh(x);return x

@router.get("/workflow-rules")
def list_workflow_rules(company_id:int=Query(...),module:str|None=None,document_type:str|None=None,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    company(db,company_id,u)
    q=select(WorkflowRule).where(WorkflowRule.tenant_id==u.tenant_id,WorkflowRule.company_id==company_id,WorkflowRule.is_active.is_(True))
    if module:q=q.where(WorkflowRule.module==module)
    if document_type:q=q.where(WorkflowRule.document_type==document_type)
    return list(db.scalars(q.order_by(WorkflowRule.id.desc())).all())

class WorkflowStartPayload(__import__("pydantic").BaseModel):
    company_id:int
    module:str
    document_type:str
    document_id:str
    delegated_to:int|None=None

@router.post("/workflow/start",status_code=201)
def start_workflow(p:WorkflowStartPayload,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    company(db,p.company_id,u)
    rule=db.scalar(select(WorkflowRule).where(WorkflowRule.tenant_id==u.tenant_id,WorkflowRule.company_id==p.company_id,WorkflowRule.module==p.module,WorkflowRule.document_type==p.document_type,WorkflowRule.is_active.is_(True)).order_by(WorkflowRule.id.desc()))
    if rule is None: raise HTTPException(404,"No active workflow rule is configured for this transaction")
    existing=db.scalar(select(WorkflowInstance).where(WorkflowInstance.tenant_id==u.tenant_id,WorkflowInstance.module==p.module,WorkflowInstance.document_type==p.document_type,WorkflowInstance.document_id==p.document_id).with_for_update())
    if existing:return existing
    w=WorkflowInstance(tenant_id=u.tenant_id,company_id=p.company_id,module=p.module,document_type=p.document_type,document_id=p.document_id,delegated_to=p.delegated_to)
    db.add(w);db.flush()
    for level in range(1,rule.approval_levels+1):
        db.add(WorkflowApprovalStep(workflow_id=w.id,level=level,status="pending"))
    db.commit();db.refresh(w);return w

@router.post("/workflow/{workflow_id}/delegate")
def delegate_workflow(workflow_id:int,delegated_to:int=Query(...,gt=0),company_id:int=Query(...),db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    company(db,company_id,u)
    w=db.scalar(select(WorkflowInstance).where(WorkflowInstance.id==workflow_id,WorkflowInstance.tenant_id==u.tenant_id,WorkflowInstance.company_id==company_id).with_for_update())
    if w is None: raise HTTPException(404,"Workflow not found")
    w.delegated_to=delegated_to;db.commit();db.refresh(w);return w
