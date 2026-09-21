from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException
from .enterprise_models import DomainControl,WorkflowRule,MasterDataIdentity,AIActionAudit,SubscriptionUsage
class EnterpriseCompletionService:
 def control(self,db,**kw):
  x=db.scalar(select(DomainControl).where(DomainControl.tenant_id==kw["tenant_id"],DomainControl.module==kw["module"],DomainControl.document_type==kw["document_type"],DomainControl.document_id==str(kw["document_id"])))
  if not x:x=DomainControl(**{**kw,"document_id":str(kw["document_id"])});db.add(x)
  else:
   for k,v in kw.items():
    if k!="tenant_id" and hasattr(x,k):setattr(x,k,v)
  db.flush();return x
 def require_approval(self,db,x):
  if x.approval_required and not x.approved:raise HTTPException(409,"Transaction requires approval before posting")
 def post(self,db,x):
  self.require_approval(db,x);x.posted=True;x.state="posted";db.flush();return x
 def reverse(self,db,x,reason):
  if not x.posted:raise HTTPException(409,"Only posted transactions can be reversed")
  x.reversed=True;x.state="reversed";x.payload={**(x.payload or {}),"reversal_reason":reason};db.flush();return x
 def ai_action(self,db,**kw):
  x=AIActionAudit(**kw);db.add(x);db.flush();return x
 def consume(self,db,tenant_id,metric,period_key,amount,limit_value=None):
  x=db.scalar(select(SubscriptionUsage).where(SubscriptionUsage.tenant_id==tenant_id,SubscriptionUsage.metric==metric,SubscriptionUsage.period_key==period_key))
  if not x:x=SubscriptionUsage(tenant_id=tenant_id,metric=metric,period_key=period_key,used=0,limit_value=limit_value);db.add(x)
  x.used=(x.used or 0)+amount
  if x.limit_value is not None and x.used>x.limit_value:raise HTTPException(402,f"Subscription usage limit exceeded for {metric}")
  db.flush();return x
enterprise_completion_service=EnterpriseCompletionService()
