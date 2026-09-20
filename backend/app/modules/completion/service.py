from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import FunctionalTransaction, TransactionApproval, PostingDiagnostic, ReconciliationItem, PeriodControl

class CompletionService:
    def register(self,db:Session,*,tenant_id:int,company_id:int,module:str,document_type:str,document_id:str,idempotency_key:str,user_id:int|None=None,source:str|None=None):
        existing=db.scalar(select(FunctionalTransaction).where(FunctionalTransaction.tenant_id==tenant_id,FunctionalTransaction.module==module,FunctionalTransaction.idempotency_key==idempotency_key))
        if existing:return existing
        tx=FunctionalTransaction(tenant_id=tenant_id,company_id=company_id,module=module,document_type=document_type,document_id=str(document_id),idempotency_key=idempotency_key,created_by=user_id,source=source)
        db.add(tx);db.flush();return tx
    def transition(self,db,tx,status,reason=None):
        allowed={"draft":{"pending_approval","posted","cancelled"},"pending_approval":{"approved","rejected","cancelled"},"approved":{"posted","cancelled"},"rejected":{"draft","cancelled"},"posted":{"reversed"},"cancelled":set(),"reversed":set()}
        if status not in allowed.get(tx.status,set()):raise HTTPException(409,f"Invalid transaction transition {tx.status} -> {status}")
        tx.status=status;tx.reason=reason;return tx
    def lock_period(self,db,company_id,period_key,module="*",reason=None):
        p=db.scalar(select(PeriodControl).where(PeriodControl.company_id==company_id,PeriodControl.period_key==period_key,PeriodControl.module==module))
        if not p:p=PeriodControl(company_id=company_id,period_key=period_key,module=module);db.add(p)
        p.is_locked=True;p.reason=reason;db.flush();return p
    def assert_open(self,db,company_id,period_key,module):
        p=db.scalar(select(PeriodControl).where(PeriodControl.company_id==company_id,PeriodControl.period_key==period_key,PeriodControl.module.in_([module,"*"]),PeriodControl.is_locked.is_(True)))
        if p:raise HTTPException(409,f"Posting period {period_key} is locked for {p.module}")
    def diagnose(self,db,**kw):
        d=PostingDiagnostic(**kw);db.add(d);db.flush();return d
    def reconcile(self,db,**kw):
        item=ReconciliationItem(**kw);db.add(item);db.flush();
        a=item.source_amount or 0;b=item.target_amount or 0;t=item.tolerance or 0
        item.status="matched" if abs(a-b)<=t else "exception";return item

completion_service=CompletionService()
