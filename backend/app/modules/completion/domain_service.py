from datetime import date, datetime, timezone
from decimal import Decimal
import hashlib, json, secrets
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.modules.commerce.models import SalesDocument, PurchaseDocument, CommercePayment, CommercePaymentAllocation
from app.modules.completion.domain_models import *
from app.modules.inventory.items.models import InventoryItem
from app.modules.inventory.warehouses.models import InventoryWarehouse
from app.modules.saas.models import Subscription

class DomainCompletionService:
    def _tenant(self, db, company_id, user):
        from app.modules.companies.models import Company
        if user.tenant_id is None: raise HTTPException(403,"User is not assigned to a tenant")
        c=db.scalar(select(Company).where(Company.id==company_id,Company.tenant_id==user.tenant_id,Company.is_active.is_(True)))
        if c is None: raise HTTPException(403,"Company is outside the current tenant")
        return c

    def aging(self, db, company_id, partner_id, direction, as_of):
        model=SalesDocument if direction=="ar" else PurchaseDocument
        positive="invoice" if direction=="ar" else "bill"
        docs=list(db.scalars(select(model).where(model.company_id==company_id,model.partner_id==partner_id,model.document_type==positive,model.status.in_({"confirmed","posted"}),model.document_date<=as_of)).all())
        result=[Decimal("0") for _ in range(5)]
        for d in docs:
            paid=Decimal("0")
            kind="sale" if direction=="ar" else "purchase"
            pays=list(db.scalars(select(CommercePayment).where(CommercePayment.company_id==company_id,CommercePayment.document_kind==kind,CommercePayment.document_id==d.id,CommercePayment.status=="posted",CommercePayment.payment_date<=as_of)).all())
            for p in pays: paid+=Decimal(p.amount or 0)
            allocs=list(db.scalars(select(CommercePaymentAllocation).where(CommercePaymentAllocation.company_id==company_id,CommercePaymentAllocation.payment_id.in_([p.id for p in pays] or [-1]),CommercePaymentAllocation.document_kind==kind,CommercePaymentAllocation.document_id==d.id,CommercePaymentAllocation.status=="active")).all())
            if allocs: paid=sum((Decimal(a.amount or 0) for a in allocs),Decimal("0"))
            outstanding=max(Decimal(d.total or 0)-paid,Decimal("0"))
            if outstanding<=0: continue
            due=d.due_date or d.document_date
            days=max((as_of-due).days,0)
            idx=0 if days==0 else 1 if days<=30 else 2 if days<=60 else 3 if days<=90 else 4
            result[idx]+=outstanding
        return result

    def save_aging(self,db,tenant_id,company_id,partner_id,direction,as_of):
        vals=self.aging(db,company_id,partner_id,direction,as_of)
        obj=db.scalar(select(FinanceAgingSnapshot).where(FinanceAgingSnapshot.company_id==company_id,FinanceAgingSnapshot.partner_id==partner_id,FinanceAgingSnapshot.direction==direction,FinanceAgingSnapshot.as_of_date==as_of))
        if obj is None: obj=FinanceAgingSnapshot(tenant_id=tenant_id,company_id=company_id,partner_id=partner_id,direction=direction,as_of_date=as_of);db.add(obj)
        obj.current_amount,obj.bucket_1_30,obj.bucket_31_60,obj.bucket_61_90,obj.bucket_91_plus=vals
        obj.total_amount=sum(vals,Decimal("0"));db.flush();return obj

    def writeoff(self,db,**kw):
        x=FinanceWriteOff(**kw);db.add(x);db.flush();return x
    def approve_writeoff(self,db,x,user_id):
        if x.status!="requested": raise HTTPException(409,"Only requested write-offs can be approved")
        x.status="approved";x.approved_by=user_id;db.flush();return x
    def post_writeoff(self,db,x,user_id):
        if x.status!="approved": raise HTTPException(409,"Write-off approval is required")
        x.status="posted";x.posted_by=user_id;db.flush();return x

    def reconcile(self,db,**kw):
        source=Decimal(str(kw["source_amount"]));target=Decimal(str(kw.get("target_amount",0)));tol=Decimal(str(kw.get("tolerance",0)));diff=source-target
        kw["difference"]=diff;kw["status"]="matched" if abs(diff)<=tol else "unmatched"
        x=FinanceReconciliation(**kw);db.add(x);db.flush();return x

    def trace(self,db,**kw):
        if kw["trace_type"]=="serial": kw["quantity"]=Decimal("1")
        x=InventoryTraceUnit(**kw);db.add(x);db.flush();return x

    def work_order(self,db,**kw):
        if db.scalar(select(ManufacturingWorkOrder).where(ManufacturingWorkOrder.company_id==kw["company_id"],ManufacturingWorkOrder.number==kw["number"])): raise HTTPException(409,"Work order number already exists")
        x=ManufacturingWorkOrder(**kw);db.add(x);db.flush();return x
    def work_order_status(self,db,x,status):
        allowed={"draft":{"released","cancelled"},"released":{"in_progress","cancelled"},"in_progress":{"completed","cancelled"},"completed":{"closed"},"closed":set(),"cancelled":set()}
        if status!=x.status and status not in allowed.get(x.status,set()): raise HTTPException(409,f"Invalid work-order transition: {x.status} -> {status}")
        x.status=status;db.flush();return x

    def crm_opportunity(self,db,**kw):
        if db.scalar(select(CRMOpportunity).where(CRMOpportunity.company_id==kw["company_id"],CRMOpportunity.code==kw["code"])): raise HTTPException(409,"Opportunity code already exists")
        x=CRMOpportunity(**kw);db.add(x);db.flush();return x

    def payroll_totals(self,db,run_id):
        run=db.scalar(select(HRPayrollCompletionRun).where(HRPayrollCompletionRun.id==run_id).with_for_update())
        if run is None: raise HTTPException(404,"Payroll run not found")
        return run

    def lifecycle(self,db,subscription_id,to_status,actor_id,reason=None):
        sub=db.scalar(select(Subscription).where(Subscription.id==subscription_id).with_for_update())
        if sub is None: raise HTTPException(404,"Subscription not found")
        old=sub.status;sub.status=to_status
        if to_status in {"cancelled","suspended","expired"}: sub.cancelled_at=datetime.now(timezone.utc) if to_status=="cancelled" else sub.cancelled_at
        e=SubscriptionLifecycleEvent(tenant_id=sub.tenant_id,subscription_id=sub.id,event_type="status_change",from_status=old,to_status=to_status,actor_id=actor_id,reason=reason);db.add(e);db.flush();return sub

    def api_key(self,db,tenant_id,company_id,name,scopes,expires_at=None):
        raw=secrets.token_urlsafe(32); prefix="pre_"+secrets.token_hex(6); digest=hashlib.sha256(raw.encode()).hexdigest()
        x=APIClientCredential(tenant_id=tenant_id,company_id=company_id,name=name,key_prefix=prefix,secret_hash=digest,scopes=json.dumps(scopes or []),expires_at=expires_at);db.add(x);db.flush();return x, f"{prefix}.{raw}"

    def mobile_enqueue(self,db,**kw):
        x=MobileSyncQueue(**kw);db.add(x);db.flush();return x

    def workflow(self,db,**kw):
        x=WorkflowInstance(**kw);db.add(x);db.flush();return x
    def workflow_decide(self,db,step,status,reason=None):
        if status not in {"approved","rejected"}: raise HTTPException(422,"Workflow decision must be approved or rejected")
        step.status=status;step.reason=reason;step.decided_at=datetime.now(timezone.utc);db.flush();return step

domain_completion_service=DomainCompletionService()
