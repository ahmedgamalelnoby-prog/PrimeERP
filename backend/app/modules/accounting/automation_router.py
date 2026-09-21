from datetime import date
from fastapi import APIRouter,Depends
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from .automation_service import accounting_automation_service
router=APIRouter(prefix="/accounting/automation",tags=["Accounting Automation"])
class AutomationCreate(BaseModel):
 company_id:int;kind:str=Field(pattern="^(accrual|deferral|recurring)$");name:str;journal_id:int;branch_id:int;start_date:date;end_date:date|None=None;frequency:str="monthly";amount:float;debit_account_id:int;credit_account_id:int;currency_code:str="EGP";description:str|None=None
@router.post("")
def create(p:AutomationCreate,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
 return accounting_automation_service.create(db,**p.model_dump())
