from datetime import date
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session
from .automation_models import JournalAutomation,JournalAllocation
from .journals.services.journal_service import journal_service
class AccountingAutomationService:
 def create(self,db,**kw):
  x=JournalAutomation(**kw);db.add(x);db.flush();return x
 def generate(self,db,*,automation:JournalAutomation,tenant_id:int,period_id:int,fiscal_year_id:int,user_id:int,entry_number:str,entry_date:date):
  lines=[{"account_combination_id":automation.debit_account_id,"debit":automation.amount,"credit":Decimal("0")},{"account_combination_id":automation.credit_account_id,"debit":Decimal("0"),"credit":automation.amount}]
  return journal_service.create_draft(db,tenant_id=tenant_id,company_id=automation.company_id,branch_id=automation.branch_id,journal_id=automation.journal_id,fiscal_year_id=fiscal_year_id,period_id=period_id,entry_number=entry_number,entry_date=entry_date,description=automation.description or automation.name,lines=lines,user_id=user_id,currency_code=automation.currency_code,source_module="accounting",source_entity=automation.kind,source_id=automation.id)
 def allocate(self,db,**kw):
  x=JournalAllocation(**kw);db.add(x);db.flush();return x
accounting_automation_service=AccountingAutomationService()
