from datetime import date,datetime
from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from .mrp_service import mrp_service
router=APIRouter(prefix="/manufacturing/mrp",tags=["manufacturing-mrp"])
@router.post("/plans")
def create_plan(plan_date:date,warehouse_id:int|None=None,notes:str|None=None,db:Session=Depends(get_db),current_user=Depends(get_current_user)):return mrp_service.create_plan(db,current_user.company_id,plan_date,warehouse_id,notes,current_user.id)
@router.post("/plans/{plan_id}/requirements")
def add_requirement(plan_id:int,item_id:int,demand:float,variant_id:int|None=None,on_hand:float=0,reserved:float=0,supply:float=0,source_type:str="demand",source_id:int|None=None,db:Session=Depends(get_db),current_user=Depends(get_current_user)):return mrp_service.add_requirement(db,current_user.company_id,plan_id,item_id,demand,variant_id,on_hand,reserved,supply,source_type,source_id)
@router.post("/plans/{plan_id}/release")
def release(plan_id:int,db:Session=Depends(get_db),current_user=Depends(get_current_user)):return mrp_service.release_plan(db,current_user.company_id,plan_id)
@router.post("/work-centers")
def work_center(code:str,name:str,capacity_hours_per_day:float=8,efficiency_percent:float=100,hourly_cost:float=0,db:Session=Depends(get_db),current_user=Depends(get_current_user)):return mrp_service.create_work_center(db,current_user.company_id,code,name,capacity_hours_per_day,efficiency_percent,hourly_cost)
@router.post("/routings")
def routing(item_id:int,work_center_id:int,sequence:int,setup_minutes:float=0,run_minutes_per_unit:float=0,queue_minutes:float=0,move_minutes:float=0,scrap_percent:float=0,variant_id:int|None=None,description:str|None=None,db:Session=Depends(get_db),current_user=Depends(get_current_user)):return mrp_service.add_routing(db,current_user.company_id,item_id,work_center_id,sequence,setup_minutes,run_minutes_per_unit,queue_minutes,move_minutes,scrap_percent,variant_id,description)
@router.post("/schedule")
def schedule(item_id:int,quantity:float,start_at:datetime,work_center_id:int,source_id:int|None=None,variant_id:int|None=None,db:Session=Depends(get_db),current_user=Depends(get_current_user)):return mrp_service.schedule(db,current_user.company_id,item_id,quantity,start_at,work_center_id,source_id,variant_id)
@router.post("/production-cost")
def production_cost(source_id:int,planned_material:float=0,actual_material:float=0,planned_labor:float=0,actual_labor:float=0,planned_overhead:float=0,actual_overhead:float=0,db:Session=Depends(get_db),current_user=Depends(get_current_user)):return mrp_service.record_cost(db,current_user.company_id,source_id,planned_material,actual_material,planned_labor,actual_labor,planned_overhead,actual_overhead)
