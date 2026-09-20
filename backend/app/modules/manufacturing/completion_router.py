from datetime import date
from fastapi import APIRouter,Depends,Query
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from .completion_service import manufacturing_completion_service

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
    x=manufacturing_completion_service.subcontract(db,company_id,work_order_id,**p.model_dump());db.commit();db.refresh(x);return x
@router.post("/work-orders/{work_order_id}/variance")
def variance(work_order_id:int,company_id:int=Query(...,gt=0),db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    x=manufacturing_completion_service.variance(db,company_id,work_order_id);db.commit();db.refresh(x);return x
