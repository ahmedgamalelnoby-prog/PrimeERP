from datetime import datetime,timezone
from decimal import Decimal
from sqlalchemy import select,func,case
from fastapi import HTTPException
from app.modules.treasury.completion_models import TreasuryTransaction,TreasuryDailyClosing,TreasuryForecast
from app.modules.companies.models import Company
from app.modules.accounting.fiscal_years.services.fiscal_year_service import fiscal_year_service
from app.modules.accounting.journals.services.journal_service import journal_service
from app.modules.commerce.accounting_models import CommerceAccountingSettings
from app.modules.accounting.chart_of_accounts.models import AccountCombination
from app.modules.branches.models import Branch
def _company(db,cid,user):
 if user.tenant_id is None: raise HTTPException(403,"User is not assigned to a tenant")
 c=db.scalar(select(Company).where(Company.id==cid,Company.tenant_id==user.tenant_id,Company.is_active.is_(True)))
 if c is None: raise HTTPException(403,"Company is outside the current tenant")
 return c
def _post(db,o,user):
 c=db.get(Company,o.company_id);s=db.scalar(select(CommerceAccountingSettings).where(CommerceAccountingSettings.company_id==o.company_id))
 if s is None: raise HTTPException(409,"Accounting configuration is required for treasury posting")
 period=fiscal_year_service.assert_open_for_date(db,company_id=o.company_id,posting_date=o.transaction_date)
 if o.transaction_type in {"receipt","deposit"}: lines=[{"account_combination_id":o.account_id,"debit":o.amount,"credit":0},{"account_combination_id":o.offset_account_id,"debit":0,"credit":o.amount}]
 elif o.transaction_type in {"payment","withdrawal"}: lines=[{"account_combination_id":o.account_id,"debit":0,"credit":o.amount},{"account_combination_id":o.offset_account_id,"debit":o.amount,"credit":0}]
 elif o.transaction_type == "transfer": lines=[{"account_combination_id":o.account_id,"debit":0,"credit":o.amount},{"account_combination_id":o.offset_account_id,"debit":o.amount,"credit":0}]
 else: raise HTTPException(422,"Unsupported treasury transaction type")
 e=journal_service.create_draft(db,tenant_id=c.tenant_id,company_id=o.company_id,branch_id=o.branch_id or s.default_branch_id,journal_id=s.cash_journal_id,fiscal_year_id=period.fiscal_year_id,period_id=period.id,entry_number=f"TR-{o.id}",entry_date=o.transaction_date,description=o.description or f"Treasury {o.transaction_type}",lines=lines,user_id=user.id,source_module="treasury",source_entity="treasury_transaction",source_id=o.id,commit=False,currency_code=o.currency)
 journal_service.submit(db,tenant_id=c.tenant_id,entry_id=e.id,user_id=user.id,commit=False)
 if not e.journal.requires_approval:
  journal_service.post(db,tenant_id=c.tenant_id,entry_id=e.id,user_id=user.id,commit=False)
  o.status="posted"
 else:
  o.status="approved"
 o.journal_entry_id=e.id;return o
def create_transaction(db,p,user):
 _company(db,p.company_id,user);fiscal_year_service.assert_open_for_date(db,company_id=p.company_id,posting_date=p.transaction_date)
 if p.account_id==p.offset_account_id:raise HTTPException(422,"Treasury accounts must be different")
 accounts=db.scalars(select(AccountCombination).where(AccountCombination.id.in_([p.account_id,p.offset_account_id]),AccountCombination.company_id==p.company_id,AccountCombination.is_active.is_(True))).all()
 if len({a.id for a in accounts}) != 2: raise HTTPException(422,"Treasury accounts must be active accounts belonging to the selected company")
 if p.branch_id is not None:
  branch=db.scalar(select(Branch).where(Branch.id==p.branch_id,Branch.company_id==p.company_id))
  if branch is None: raise HTTPException(422,"Branch is outside the selected company")
 o=TreasuryTransaction(company_id=p.company_id,branch_id=p.branch_id,transaction_date=p.transaction_date,transaction_type=p.transaction_type,account_id=p.account_id,offset_account_id=p.offset_account_id,amount=p.amount,currency=p.currency,reference=p.reference,description=p.description,status="pending_approval" if p.requires_approval else "approved",approval_status="pending" if p.requires_approval else "approved",created_by=user.id);db.add(o);db.flush()
 if not p.requires_approval:_post(db,o,user)
 return o
def list_transactions(db,cid,user,status=None,transaction_type=None):
 _company(db,cid,user)
 q=select(TreasuryTransaction).where(TreasuryTransaction.company_id==cid).order_by(TreasuryTransaction.transaction_date.desc(),TreasuryTransaction.id.desc())
 if status: q=q.where(TreasuryTransaction.status==status)
 if transaction_type: q=q.where(TreasuryTransaction.transaction_type==transaction_type)
 return list(db.scalars(q).all())

def reverse_transaction(db,o,user):
 if o.status!="posted": raise HTTPException(409,"Only posted treasury transactions can be reversed")
 _company(db,o.company_id,user)
 existing=db.scalar(select(TreasuryTransaction).where(TreasuryTransaction.company_id==o.company_id,TreasuryTransaction.reference==f"REV-TX-{o.id}"))
 if existing is not None: raise HTTPException(409,"Treasury transaction is already reversed")
 reverse_type={"receipt":"payment","payment":"receipt","deposit":"withdrawal","withdrawal":"deposit","transfer":"transfer"}[o.transaction_type]
 reverse_account=o.offset_account_id if o.transaction_type=="transfer" else o.account_id
 reverse_offset=o.account_id if o.transaction_type=="transfer" else o.offset_account_id
 p=type("ReversalPayload",(),{"company_id":o.company_id,"branch_id":o.branch_id,"transaction_date":o.transaction_date,"transaction_type":reverse_type,"account_id":reverse_account,"offset_account_id":reverse_offset,"amount":o.amount,"currency":o.currency,"reference":f"REV-TX-{o.id}","description":f"Reversal of treasury transaction {o.id}","requires_approval":False})()
 return create_transaction(db,p,user)

def decide(db,o,approve,user):
 if o.status!="pending_approval":raise HTTPException(409,"Transaction is not pending approval")
 if not approve:o.status="cancelled";o.approval_status="rejected";return o
 o.status="approved";o.approval_status="approved";o.approved_by=user.id;o.approved_at=datetime.now(timezone.utc);return _post(db,o,user)
def daily_close(db,p,user):
 _company(db,p.company_id,user);sign=case((TreasuryTransaction.transaction_type.in_(["receipt","deposit"]),TreasuryTransaction.amount),(TreasuryTransaction.transaction_type.in_(["payment","withdrawal"]),-TreasuryTransaction.amount),else_=0);q=select(func.coalesce(func.sum(sign),0)).where(TreasuryTransaction.company_id==p.company_id,TreasuryTransaction.branch_id==p.branch_id,TreasuryTransaction.transaction_date<=p.closing_date,TreasuryTransaction.status=="posted");book=db.scalar(q) or 0;o=db.scalar(select(TreasuryDailyClosing).where(TreasuryDailyClosing.company_id==p.company_id,TreasuryDailyClosing.branch_id==p.branch_id,TreasuryDailyClosing.closing_date==p.closing_date).with_for_update())
 if o is not None and o.status=="closed":raise HTTPException(409,"Treasury day is already closed")
 if o is None:o=TreasuryDailyClosing(company_id=p.company_id,branch_id=p.branch_id,closing_date=p.closing_date);db.add(o)
 o.book_balance=book;o.counted_balance=p.counted_balance;o.difference=p.counted_balance-book;o.status="closed";o.closed_by=user.id;o.closed_at=datetime.now(timezone.utc);o.notes=p.notes;db.flush();return o
def forecast(db,p,user):
 _company(db,p.company_id,user)
 existing=db.scalar(select(TreasuryForecast).where(TreasuryForecast.company_id==p.company_id,TreasuryForecast.forecast_date==p.forecast_date,TreasuryForecast.source==p.source))
 if existing is not None:
  existing.expected_inflow=p.expected_inflow;existing.expected_outflow=p.expected_outflow;existing.opening_balance=p.opening_balance;existing.closing_balance=p.opening_balance+p.expected_inflow-p.expected_outflow;db.flush();return existing
 o=TreasuryForecast(company_id=p.company_id,forecast_date=p.forecast_date,expected_inflow=p.expected_inflow,expected_outflow=p.expected_outflow,opening_balance=p.opening_balance,closing_balance=p.opening_balance+p.expected_inflow-p.expected_outflow,source=p.source,created_by=user.id);db.add(o);db.flush();return o
def positions(db,cid,user):
 _company(db,cid,user)
 debit=func.sum(case((TreasuryTransaction.transaction_type.in_(["receipt","deposit"]),TreasuryTransaction.amount),(TreasuryTransaction.transaction_type.in_(["payment","withdrawal"]),-TreasuryTransaction.amount),(TreasuryTransaction.transaction_type=="transfer",-TreasuryTransaction.amount),else_=0))
 rows=db.execute(select(TreasuryTransaction.account_id,debit.label("balance")).where(TreasuryTransaction.company_id==cid,TreasuryTransaction.status=="posted").group_by(TreasuryTransaction.account_id)).all()
 result={a:Decimal(str(b or 0)) for a,b in rows}
 transfer_rows=db.execute(select(TreasuryTransaction.offset_account_id,func.sum(TreasuryTransaction.amount)).where(TreasuryTransaction.company_id==cid,TreasuryTransaction.status=="posted",TreasuryTransaction.transaction_type=="transfer").group_by(TreasuryTransaction.offset_account_id)).all()
 for account_id,amount in transfer_rows:
  result[account_id]=result.get(account_id,Decimal("0"))+Decimal(str(amount or 0))
 return [{"account_id":a,"balance":b} for a,b in result.items()]
