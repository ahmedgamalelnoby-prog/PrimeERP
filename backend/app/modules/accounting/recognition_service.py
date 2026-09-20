from calendar import monthrange
from datetime import date
from decimal import Decimal,ROUND_HALF_UP
from sqlalchemy import select
from fastapi import HTTPException
from app.modules.accounting.recognition_models import AccountingRecognitionSchedule
from app.modules.accounting.journals.services.journal_service import journal_service
from app.modules.accounting.fiscal_years.repositories.fiscal_year_repository import fiscal_year_repository
class AccountingRecognitionService:
 def create(self,db,user,**kw):
  if user.tenant_id is None:raise HTTPException(status_code=409,detail="User is not assigned to a tenant")
  if kw["period_count"]<=0 or kw["total_amount"]<=0:raise HTTPException(status_code=422,detail="Recognition amount and period count must be positive")
  if kw["kind"] not in {"accrual","deferral","recurring"}:raise HTTPException(status_code=422,detail="Invalid recognition type")
  x=AccountingRecognitionSchedule(tenant_id=user.tenant_id,**kw);db.add(x);db.flush();return x
 def run(self,db,user,schedule_id,run_date):
  x=db.scalar(select(AccountingRecognitionSchedule).where(AccountingRecognitionSchedule.id==schedule_id,AccountingRecognitionSchedule.tenant_id==user.tenant_id).with_for_update())
  if not x:raise HTTPException(status_code=404,detail="Recognition schedule not found")
  if not x.active:raise HTTPException(status_code=409,detail="Recognition schedule is inactive")
  if x.recognized_periods>=x.period_count: x.active=False;db.flush();raise HTTPException(status_code=409,detail="Recognition schedule is complete")
  if run_date<x.next_run_date:raise HTTPException(status_code=409,detail="Schedule is not due yet")
  p=fiscal_year_repository.get_period_for_date(db,user.tenant_id,x.company_id,run_date)
  if not p:raise HTTPException(status_code=409,detail="No open accounting period exists for recognition date")
  remaining=Decimal(str(x.total_amount))-Decimal(str(x.total_amount))*Decimal(x.recognized_periods)/Decimal(x.period_count)
  if x.recognized_periods==x.period_count-1:amount=remaining
  else:amount=(Decimal(str(x.total_amount))/Decimal(x.period_count)).quantize(Decimal("0.000001"),rounding=ROUND_HALF_UP)
  entry=journal_service.create_draft(db,tenant_id=user.tenant_id,company_id=x.company_id,branch_id=x.branch_id,journal_id=x.journal_id,fiscal_year_id=p.fiscal_year_id,period_id=p.id,entry_number=f"{x.kind.upper()}-{x.id}-{x.recognized_periods+1}",entry_date=run_date,description=f"{x.name} recognition {x.recognized_periods+1}/{x.period_count}",lines=[{"account_combination_id":x.debit_account_id,"debit":amount,"credit":0},{"account_combination_id":x.credit_account_id,"debit":0,"credit":amount}],user_id=user.id,currency_code=x.currency_code,source_module="accounting",source_entity=x.kind,source_id=x.id)
  if entry.journal.requires_approval:journal_service.submit(db,tenant_id=user.tenant_id,entry_id=entry.id,user_id=user.id);x.recognized_periods+=1;x.active=x.recognized_periods<x.period_count;db.flush();return entry
  journal_service.post(db,tenant_id=user.tenant_id,entry_id=entry.id,user_id=user.id)
  x.recognized_periods+=1
  if x.recognized_periods>=x.period_count:x.active=False
  else:
   y=x.next_run_date.year+(x.next_run_date.month//12);m=x.next_run_date.month%12+1;x.next_run_date=date(y,m,min(x.next_run_date.day,monthrange(y,m)[1]))
  db.flush();return entry
recognition_service=AccountingRecognitionService()
