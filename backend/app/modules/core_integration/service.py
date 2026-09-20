from sqlalchemy import select
from fastapi import HTTPException
from app.modules.core_integration.models import IntegrationTransaction
class CoreIntegrationService:
 def begin(self,db,*,user,company_id,source_module,source_entity,source_id,operation,idempotency_key):
  existing=db.scalar(select(IntegrationTransaction).where(IntegrationTransaction.company_id==company_id,IntegrationTransaction.idempotency_key==idempotency_key).with_for_update())
  if existing:return existing,False
  if user.tenant_id is None:raise HTTPException(403,"Tenant context is required")
  x=IntegrationTransaction(tenant_id=user.tenant_id,company_id=company_id,source_module=source_module,source_entity=source_entity,source_id=str(source_id),operation=operation,idempotency_key=idempotency_key,actor_id=user.id);db.add(x);db.flush();return x,True
 def complete(self,db,x,status="completed"):
  x.status=status;db.flush();return x
 def reverse(self,db,x,user,reason):
  if x.reversed:raise HTTPException(409,"Transaction is already reversed")
  if x.status!="completed":raise HTTPException(409,"Only completed transactions can be reversed")
  r=IntegrationTransaction(tenant_id=x.tenant_id,company_id=x.company_id,source_module=x.source_module,source_entity=x.source_entity,source_id=x.source_id,operation="reverse:"+x.operation,idempotency_key=f"reverse:{x.id}",reversal_of_id=x.id,reason=reason,actor_id=user.id,status="completed");db.add(r);x.reversed=True;db.flush();return r
core_integration_service=CoreIntegrationService()
