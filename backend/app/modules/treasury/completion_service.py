from datetime import datetime,timezone
from sqlalchemy import select,func
from fastapi import HTTPException
from app.modules.treasury.completion_models import TreasuryTransaction,TreasuryDailyClosing,TreasuryForecast
from app.modules.companies.models import Company
from app.modules.accounting.fiscal_years.services.fiscal_year_service import fiscal_year_service
from app.modules.accounting.journals.services.journal_service import journal_service
from app.modules.commerce.accounting_models import CommerceAccountingSettings
def _company(db,cid,user):
 if user.tenant_id is None: raise HTTPException(403,"User is not assigned to a tenant")
 c=db.scalar(select(Company).where(Company.id==cid,Company.tenant_id==user.tenant_id,Company.is_active.is_(True)))
 if c is None: raise HTTPException(403,"Company is outside the current tenant")
 return c
def _post(db,o,user):
 c=db.get(Company,o.company_id); s=db.scalar(select(CommerceAccountingSettings).where(CommerceAccountingSettings.company_id==o.company_id))
 if s is None: raise HTTPException(409,"Accounting configuration is required for treasury posting")
 period=fiscal_year_service.assert_open_for_date(db,company_id=o.company_id,posting_date=o.transaction_date)
 debit_first=o.transaction_type in {"receipt","deposit"}
 lines=[{"account_combination_id":o.account_id,"debit":o.amount if debit_first else 0,"credit":o.amount if not debit_first else 0},{"account_combination_id":o.offset_account_id,"debit":o.amount if not debit_first else 0,"credit":o.amount if debit_first else 0}]
 e=journal_service.create_draft(db,tenant_id=c.tenant_id,company_id=o.company_id,branch_id=o.branch_id or s.default_branch_id,journal_id=s.cash_journal_id,fiscal_year_id=period.fiscal_year_id,period_id=period.id,entry_number=f"TR-{o.id}",entry_date=o.transaction_date,description=o.description or f"Treasury {o.transaction_type}",lines=lines,user_id=user.id,source_module="treasury",source_entity="treasury_transaction",source_id=str(o.id),commit=False,currency_code=o.currency)
 journal_service.submit(db,tenant_id=c.tenant_id,entry_id=e.id,user_id=user.id,commit=False)
 if not e.journal.requires_approval: journal_service.post(db,tenant_id=c.tenant_id,entry_id=e.id,user_id=user.id,commit=False)
 o.journal_entry_id=e.id;o.status="posted";return o
def create_transaction(db,p,user):
 _company(db,p.company_id,user);fiscal_year_service.assert_open_for_date(db,company_id=p.company_id,posting_date=p.transaction_date)
 if p.account_id==p.offset_account_id: raise HTTPException(422,"Treasury accounts must be different")
 o=TreasuryTransaction(company_id=p.company_id,branch_id=p.branch_id,transaction_date=p.transaction_date,transaction_type=p.transaction_type,account_id=p.account_id,offset_account_id=p.offset_account_id,amount=p.amount,currency=p.currency,reference=p.reference,description=p.description,status="pending_approval" if p.requires_approval else "approved",approval_status="pending" if p.requires_approval else "approved",created_by=user.id)
 db.add(o);db.flush()
 if not p.requires_approval:_post(db,o,user)
 return o
def decide(db,o,approve,user):
 if o.status!="pending_approval": raise HTTPException(409,"Transaction is not pending approval")
 if not approve:o.status="cancelled";o.approval_status="rejected";return o
 o.status="approved";o.approval_status="approved";o.approved_by=user.id;o.approved_at=datetime.now(timezone.utc);return _post(db,o,user)
def daily_close(db,p,user):
 _company(db,p.company_id,user);q=select(func.coalesce(func.sum(TreasuryTransaction.amount),0)).where(TreasuryTransaction.company_id==p.company_id,TreasuryTransaction.branch_id==p.branch_id,TreasuryTransaction.transaction_date<=p.closing_date,TreasuryTransaction.status=="posted");book=db.scalar(q) or 0;o=TreasuryDailyClosing(company_id=p.company_id,branch_id=p.branch_id,closing_date=p.closing_date,book_balance=book,counted_balance=p.counted_balance,difference=p.counted_balance-book,status="closed",closed_by=user.id,closed_at=datetime.now(timezone.utc),notes=p.notes);db.add(o);db.flush();return o
def forecast(db,p,user):
 _company(db,p.company_id,user);o=TreasuryForecast(company_id=p.company_id,forecast_date=p.forecast_date,expected_inflow=p.expected_inflow,expected_outflow=p.expected_outflow,opening_balance=p.opening_balance,closing_balance=p.opening_balance+p.expected_inflow-p.expected_outflow,source=p.source,created_by=user.id);db.add(o);db.flush();return o
def positions(db,cid,user):
 _company(db,cid,user);rows=db.execute(select(TreasuryTransaction.account_id,func.sum(TreasuryTransaction.amount)).where(TreasuryTransaction.company_id==cid,TreasuryTransaction.status=="posted").group_by(TreasuryTransaction.account_id)).all();return [{"account_id":a,"balance":b} for a,b in rows]
