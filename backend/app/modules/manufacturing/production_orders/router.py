from datetime import date
from decimal import Decimal
from fastapi import APIRouter,Depends,Query
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.manufacturing.production_orders.service import manufacturing_production_service
from app.modules.manufacturing.completion_service import manufacturing_completion_service
router=APIRouter(prefix="/manufacturing/work-orders",tags=["Manufacturing Work Orders"])
class WorkOrderCreate(BaseModel):
 company_id:int=Field(gt=0);number:str=Field(min_length=1,max_length=80);item_id:int=Field(gt=0);variant_id:int|None=Field(default=None,gt=0);recipe_id:int|None=Field(default=None,gt=0);warehouse_id:int|None=Field(default=None,gt=0);planned_qty:Decimal=Field(gt=0);planned_start:date|None=None;planned_end:date|None=None
class StatusPayload(BaseModel): status:str=Field(pattern="^(released|in_progress|completed|closed|cancelled)$")
class ConsumePayload(BaseModel): source_location_id:int=Field(gt=0);item_id:int=Field(gt=0);variant_id:int|None=Field(default=None,gt=0);quantity:Decimal=Field(gt=0);unit_cost:Decimal=Field(default=0,ge=0)
class CompletePayload(BaseModel): destination_location_id:int=Field(gt=0);completed_qty:Decimal=Field(gt=0);output_unit_cost:Decimal|None=Field(default=None,gt=0)
@router.post("",status_code=201)
def create(p:WorkOrderCreate,u:User=Depends(get_current_user),db:Session=Depends(get_db)):
 x=manufacturing_production_service.create(db,tenant_id=u.tenant_id,user_id=u.id,**p.model_dump());db.commit();db.refresh(x);return x
@router.post("/{work_order_id}/transition")
def transition(work_order_id:int,p:StatusPayload,company_id:int=Query(...,gt=0),u:User=Depends(get_current_user),db:Session=Depends(get_db)):
 x=manufacturing_production_service.transition(db,u.tenant_id,company_id,work_order_id,p.status);db.commit();db.refresh(x);return x
@router.get("/{work_order_id}/explosion")
def explosion(work_order_id:int,company_id:int=Query(...,gt=0),quantity:Decimal|None=Query(None,gt=0),u:User=Depends(get_current_user),db:Session=Depends(get_db)):
 from sqlalchemy import select
 from app.modules.completion.domain_models import ManufacturingWorkOrder
 x=db.scalar(select(ManufacturingWorkOrder).where(ManufacturingWorkOrder.id==work_order_id,ManufacturingWorkOrder.company_id==company_id))
 if x is None: from fastapi import HTTPException;raise HTTPException(404,"Work order not found")
 return manufacturing_production_service.explode(db,company_id,x.recipe_id,quantity or x.planned_qty) if x.recipe_id else []
@router.post("/{work_order_id}/consume")
def consume(work_order_id:int,p:ConsumePayload,company_id:int=Query(...,gt=0),u:User=Depends(get_current_user),db:Session=Depends(get_db)):
 x=manufacturing_production_service.consume(db,u.tenant_id,u.id,company_id,work_order_id,**p.model_dump());db.commit();db.refresh(x);return x
@router.post("/{work_order_id}/complete")
def complete(work_order_id:int,p:CompletePayload,company_id:int=Query(...,gt=0),u:User=Depends(get_current_user),db:Session=Depends(get_db)):
 result=manufacturing_completion_service.execute_production(db,u.tenant_id,company_id,work_order_id,u.id,p.completed_qty,None,p.destination_location_id);db.commit();return result
