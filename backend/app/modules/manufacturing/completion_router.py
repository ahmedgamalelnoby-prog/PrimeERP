from datetime import date
from fastapi import APIRouter,Depends,Query,HTTPException
from pydantic import BaseModel,Field
from decimal import Decimal
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from .completion_service import manufacturing_completion_service
from app.modules.completion.domain_models import ManufacturingWorkOrder
from app.modules.accounting.journals.services.journal_service import journal_service

router=APIRouter(prefix="/manufacturing/completion",tags=["Manufacturing Completion"])

class Labor(BaseModel):
    work_date:date
    user_id:int|None=None
    minutes:float=Field(gt=0)
    hourly_rate:float=Field(ge=0)
class Overhead(BaseModel):
    cost_code:str=Field(min_length=1,max_length=80)
    amount:float=Field(ge=0)
    description:str|None=None
class Scrap(BaseModel):
    item_id:int=Field(gt=0);variant_id:int|None=None;quantity:float=Field(gt=0);unit_cost:float=Field(ge=0);reason:str=Field(min_length=1,max_length=300);stock_move_id:int|None=None
class ByProduct(BaseModel):
    item_id:int=Field(gt=0);variant_id:int|None=None;quantity:float=Field(gt=0);unit_cost:float=Field(ge=0);stock_move_id:int|None=None
class GLVariance(BaseModel):
    journal_id:int=Field(gt=0);fiscal_year_id:int=Field(gt=0);period_id:int=Field(gt=0);branch_id:int=Field(gt=0);entry_number:str=Field(min_length=1,max_length=80);entry_date:date;debit_account_id:int=Field(gt=0);credit_account_id:int=Field(gt=0)
class Subcontract(BaseModel):
    vendor_id:int=Field(gt=0);service_reference:str=Field(min_length=1,max_length=120);planned_quantity:float=Field(gt=0);actual_quantity:float=Field(ge=0);unit_cost:float=Field(ge=0);status:str="planned"

@router.post("/work-orders/{work_order_id}/labor")
def labor(work_order_id:int,p:Labor,company_id:int=Query(...,gt=0),db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    x=manufacturing_completion_service.labor(db,company_id,work_order_id,**p.model_dump());db.commit();db.refresh(x);return x
@router.post("/work-orders/{work_order_id}/overhead")
def overhead(work_order_id:int,p:Overhead,company_id:int=Query(...,gt=0),db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    x=manufacturing_completion_service.overhead(db,company_id,work_order_id,**p.model_dump());db.commit();db.refresh(x);return x
@router.post("/work-orders/{work_order_id}/scrap")
def scrap(work_order_id:int,p:Scrap,company_id:int=Query(...,gt=0),db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    x=manufacturing_completion_service.scrap(db,company_id,work_order_id,**p.model_dump());db.commit();db.refresh(x);return x
@router.post("/work-orders/{work_order_id}/byproducts")
def byproducts(work_order_id:int,p:ByProduct,company_id:int=Query(...,gt=0),db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    x=manufacturing_completion_service.byproduct(db,company_id,work_order_id,**p.model_dump());db.commit();db.refresh(x);return x
@router.post("/work-orders/{work_order_id}/subcontract")
def subcontract(work_order_id:int,p:Subcontract,company_id:int=Query(...,gt=0),db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    if p.actual_quantity > p.planned_quantity and p.status != "received": raise HTTPException(422,"Actual subcontract quantity cannot exceed planned quantity unless received")
    x=manufacturing_completion_service.subcontract(db,company_id,work_order_id,**p.model_dump());db.commit();db.refresh(x);return x
@router.post("/work-orders/{work_order_id}/variance")
def variance(work_order_id:int,company_id:int=Query(...,gt=0),db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    x=manufacturing_completion_service.variance(db,company_id,work_order_id);db.commit();db.refresh(x);return x

@router.post("/work-orders/{work_order_id}/variance/post")
def post_variance(work_order_id:int,p:GLVariance,company_id:int=Query(...,gt=0),db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    x=manufacturing_completion_service.post_variance(db,company_id,work_order_id,tenant_id=u.tenant_id,user_id=u.id,**p.model_dump());db.commit();db.refresh(x);return x

class Settlement(BaseModel):
    journal_id:int=Field(gt=0);fiscal_year_id:int=Field(gt=0);period_id:int=Field(gt=0);branch_id:int=Field(gt=0);entry_number:str=Field(min_length=1,max_length=80);entry_date:date;wip_account_id:int=Field(gt=0);finished_goods_account_id:int=Field(gt=0)

@router.post("/work-orders/{work_order_id}/wip/settle")
def settle_wip(work_order_id:int,p:Settlement,company_id:int=Query(...,gt=0),db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    wo=db.get(ManufacturingWorkOrder,work_order_id)
    if wo is None or wo.company_id != company_id: raise HTTPException(404,"Work order not found")
    v=manufacturing_completion_service.variance(db,company_id,work_order_id)
    if v.wip_journal_entry_id: raise HTTPException(409,"WIP is already settled")
    total=Decimal(v.actual_material or 0)+Decimal(v.actual_labor or 0)+Decimal(v.actual_overhead or 0)-Decimal(v.byproduct_credit or 0)
    if total <= 0: raise HTTPException(409,"No positive WIP balance to settle")
    entry=journal_service.create_draft(db,tenant_id=u.tenant_id,company_id=company_id,branch_id=p.branch_id,journal_id=p.journal_id,fiscal_year_id=p.fiscal_year_id,period_id=p.period_id,entry_number=p.entry_number,entry_date=p.entry_date,description=f"WIP settlement for work order {work_order_id}",lines=[{"account_combination_id":p.wip_account_id,"debit":0,"credit":total},{"account_combination_id":p.finished_goods_account_id,"debit":total,"credit":0}],user_id=u.id,source_module="manufacturing",source_entity="wip_settlement",source_id=work_order_id,commit=False)
    journal_service.submit(db,tenant_id=u.tenant_id,entry_id=entry.id,user_id=u.id,commit=False);journal_service.post(db,tenant_id=u.tenant_id,entry_id=entry.id,user_id=u.id,commit=False)
    v.wip_journal_entry_id=entry.id;db.commit();db.refresh(v);return v
