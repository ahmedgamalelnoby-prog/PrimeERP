from datetime import date
from decimal import Decimal
from fastapi import APIRouter,Depends
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from .recognition_service import recognition_service
router=APIRouter(prefix="/accounting/recognition",tags=["Accounting Recognition"])
class RecognitionCreate(BaseModel):
 company_id:int;kind:str=Field(pattern="^(accrual|deferral|recurring)$");name:str;journal_id:int;branch_id:int;debit_account_id:int;credit_account_id:int;total_amount:Decimal=Field(gt=0);period_count:int=Field(gt=0);next_run_date:date;end_date:date|None=None;currency_code:str="EGP";source_reference:str|None=None
@router.post("")
def create(p:RecognitionCreate,db:Session=Depends(get_db),u:User=Depends(get_current_user)):return recognition_service.create(db,u,**p.model_dump())
@router.post("/{schedule_id}/run")
def run(schedule_id:int,run_date:date,db:Session=Depends(get_db),u:User=Depends(get_current_user)):return recognition_service.run(db,u,schedule_id,run_date)
