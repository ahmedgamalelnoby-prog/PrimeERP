from datetime import date
from decimal import Decimal
from fastapi import APIRouter,Depends
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from .advanced_service import accounting_advanced_service
router=APIRouter(prefix="/accounting/advanced",tags=["Accounting Advanced"])
class AutoRule(BaseModel): company_id:int;name:str;source_module:str;source_entity:str;journal_id:int;branch_id:int;debit_account_id:int;credit_account_id:int;currency_code:str="EGP";auto_approve:bool=True;auto_post:bool=True
class AutoPost(BaseModel): company_id:int;branch_id:int;journal_id:int;when:date;source_module:str;source_entity:str;source_id:int;debit_account_id:int;credit_account_id:int;amount:Decimal=Field(gt=0);description:str;currency_code:str="EGP"
class FX(BaseModel): company_id:int;branch_id:int;journal_id:int;gain_loss_account_id:int;foreign_account_id:int;when:date;currency_code:str=Field(min_length=3,max_length=3);foreign_amount:Decimal=Field(gt=0);old_rate:Decimal=Field(gt=0);new_rate:Decimal=Field(gt=0)
class Intercompany(BaseModel): source_company_id:int;target_company_id:int;source_branch_id:int;target_branch_id:int;source_journal_id:int;target_journal_id:int;when:date;amount:Decimal=Field(gt=0);source_debit_account_id:int;source_credit_account_id:int;target_debit_account_id:int;target_credit_account_id:int;reference:str;description:str
class Elimination(BaseModel): company_id:int;branch_id:int;journal_id:int;when:date;debit_account_id:int;credit_account_id:int;amount:Decimal=Field(gt=0);consolidation_key:str;description:str
@router.post("/auto-rules")
def auto_rule(p:AutoRule,db:Session=Depends(get_db),u:User=Depends(get_current_user)):return accounting_advanced_service.create_rule(db,u,**p.model_dump())
@router.post("/auto-post")
def auto_post(p:AutoPost,db:Session=Depends(get_db),u:User=Depends(get_current_user)):return accounting_advanced_service.post_source(db,u,**p.model_dump())
@router.post("/fx-revaluation")
def fx(p:FX,db:Session=Depends(get_db),u:User=Depends(get_current_user)):return accounting_advanced_service.fx_revalue(db,u,**p.model_dump())
@router.post("/intercompany")
def ic(p:Intercompany,db:Session=Depends(get_db),u:User=Depends(get_current_user)):return accounting_advanced_service.intercompany(db,u,**p.model_dump())
@router.post("/eliminations")
def elimination(p:Elimination,db:Session=Depends(get_db),u:User=Depends(get_current_user)):return accounting_advanced_service.eliminate(db,u,**p.model_dump())
@router.get("/diagnostics")
def diagnostics(company_id:int,start_date:date|None=None,end_date:date|None=None,db:Session=Depends(get_db),u:User=Depends(get_current_user)):return accounting_advanced_service.diagnostics(db,u,company_id=company_id,start_date=start_date,end_date=end_date)
@router.get("/drilldown/{account_id}")
def drilldown(account_id:int,company_id:int,start_date:date|None=None,end_date:date|None=None,db:Session=Depends(get_db),u:User=Depends(get_current_user)):return accounting_advanced_service.drilldown(db,u,company_id=company_id,account_id=account_id,start_date=start_date,end_date=end_date)
