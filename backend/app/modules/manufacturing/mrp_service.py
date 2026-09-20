from datetime import datetime,timedelta,timezone
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException
from .mrp_models import MRPPlan,MRPRequirement,MRPWorkCenter,MRPRoutingOperation,MRPScheduleSlot,MRPProductionCost
from app.modules.catalog.models import Recipe
from app.modules.manufacturing.production_orders.service import manufacturing_production_service
class MRPService:
 def create_plan(self,db,company_id,plan_date,warehouse_id=None,notes=None,user_id=None):
  x=MRPPlan(company_id=company_id,plan_date=plan_date,warehouse_id=warehouse_id,notes=notes,created_by=user_id);db.add(x);db.flush();return x
 def add_requirement(self,db,company_id,plan_id,item_id,demand,variant_id=None,on_hand=0,reserved=0,supply=0,source_type="demand",source_id=None,tenant_id=None,user_id=None):
  plan=db.scalar(select(MRPPlan).where(MRPPlan.id==plan_id,MRPPlan.company_id==company_id).with_for_update())
  if not plan:raise HTTPException(404,"MRP plan not found")
  d=Decimal(demand);available=Decimal(on_hand)-Decimal(reserved);short=max(d-available-Decimal(supply),Decimal(0))
  x=MRPRequirement(plan_id=plan_id,item_id=item_id,variant_id=variant_id,demand_quantity=d,on_hand_quantity=on_hand,reserved_quantity=reserved,supply_quantity=supply,shortage_quantity=short,suggested_quantity=short,source_type=source_type,source_id=source_id);db.add(x);db.flush()
  if short>0 and tenant_id is not None and user_id is not None:
   recipe_q=select(Recipe.id).where(Recipe.company_id==company_id,Recipe.product_id==item_id,Recipe.is_active.is_(True))
   if variant_id is not None: recipe_q=recipe_q.where(Recipe.variant_id==variant_id)
   else: recipe_q=recipe_q.where(Recipe.variant_id.is_(None))
   recipe_id=db.scalar(recipe_q.order_by(Recipe.version.desc()))
   wo=manufacturing_production_service.create(db,tenant_id=tenant_id,user_id=user_id,company_id=company_id,number=f"MRP-{plan.id}-{x.id}",item_id=item_id,variant_id=variant_id,recipe_id=recipe_id,warehouse_id=plan.warehouse_id,planned_qty=short,planned_start=plan.plan_date,planned_end=plan.plan_date)
   x.production_order_id=wo.id;x.supply_quantity=Decimal(x.supply_quantity or 0)+short;x.shortage_quantity=max(d-Decimal(x.on_hand_quantity or 0)-Decimal(x.reserved_quantity or 0)-Decimal(x.supply_quantity or 0),Decimal(0));x.suggested_quantity=x.shortage_quantity
  return x
 def release_plan(self,db,company_id,plan_id):
  x=db.scalar(select(MRPPlan).where(MRPPlan.id==plan_id,MRPPlan.company_id==company_id).with_for_update())
  if not x:raise HTTPException(404,"MRP plan not found")
  if x.status not in {"draft","approved"}:raise HTTPException(409,"Plan cannot be released")
  x.status="released";return x
 def create_work_center(self,db,company_id,code,name,capacity_hours_per_day=8,efficiency_percent=100,hourly_cost=0):
  x=MRPWorkCenter(company_id=company_id,code=code,name=name,capacity_hours_per_day=capacity_hours_per_day,efficiency_percent=efficiency_percent,hourly_cost=hourly_cost);db.add(x);db.flush();return x
 def add_routing(self,db,company_id,item_id,work_center_id,sequence,setup_minutes=0,run_minutes_per_unit=0,queue_minutes=0,move_minutes=0,scrap_percent=0,variant_id=None,description=None):
  wc=db.scalar(select(MRPWorkCenter).where(MRPWorkCenter.id==work_center_id,MRPWorkCenter.company_id==company_id,MRPWorkCenter.status=="active"))
  if not wc:raise HTTPException(404,"Work center not found")
  x=MRPRoutingOperation(company_id=company_id,item_id=item_id,variant_id=variant_id,sequence=sequence,work_center_id=work_center_id,setup_minutes=setup_minutes,run_minutes_per_unit=run_minutes_per_unit,queue_minutes=queue_minutes,move_minutes=move_minutes,scrap_percent=scrap_percent,description=description);db.add(x);db.flush();return x
 def schedule(self,db,company_id,item_id,quantity,start_at,work_center_id,source_id=None,variant_id=None):
  wc=db.scalar(select(MRPWorkCenter).where(MRPWorkCenter.id==work_center_id,MRPWorkCenter.company_id==company_id,MRPWorkCenter.status=="active"))
  if not wc:raise HTTPException(404,"Work center not found")
  ops=list(db.scalars(select(MRPRoutingOperation).where(MRPRoutingOperation.company_id==company_id,MRPRoutingOperation.item_id==item_id,MRPRoutingOperation.variant_id==variant_id).order_by(MRPRoutingOperation.sequence)).all())
  minutes=Decimal("0")
  for op in ops:minutes+=Decimal(op.setup_minutes or 0)+Decimal(op.run_minutes_per_unit or 0)*Decimal(quantity)+Decimal(op.queue_minutes or 0)+Decimal(op.move_minutes or 0)
  if minutes<=0:minutes=(Decimal(quantity)/Decimal(wc.capacity_hours_per_day))*Decimal(60)
  duration=timedelta(minutes=float(minutes/Decimal(max(Decimal(wc.efficiency_percent or 100)/100,Decimal("0.01")))))
  end=start_at+duration
  overlap=db.scalar(select(MRPScheduleSlot).where(MRPScheduleSlot.company_id==company_id,MRPScheduleSlot.work_center_id==work_center_id,MRPScheduleSlot.status.in_({"planned","released","in_progress"}),MRPScheduleSlot.start_at<end,MRPScheduleSlot.end_at>start_at))
  if overlap:raise HTTPException(409,"Work center capacity conflict")
  x=MRPScheduleSlot(company_id=company_id,work_center_id=work_center_id,item_id=item_id,variant_id=variant_id,source_id=source_id,start_at=start_at,end_at=end,planned_quantity=quantity);db.add(x);db.flush();return x
 def record_cost(self,db,company_id,source_id,planned_material=0,actual_material=0,planned_labor=0,actual_labor=0,planned_overhead=0,actual_overhead=0):
  x=db.scalar(select(MRPProductionCost).where(MRPProductionCost.company_id==company_id,MRPProductionCost.source_id==source_id).with_for_update())
  if not x:x=MRPProductionCost(company_id=company_id,source_id=source_id);db.add(x)
  x.planned_material=planned_material;x.actual_material=actual_material;x.planned_labor=planned_labor;x.actual_labor=actual_labor;x.planned_overhead=planned_overhead;x.actual_overhead=actual_overhead
  x.variance_material=Decimal(actual_material)-Decimal(planned_material);x.variance_labor=Decimal(actual_labor)-Decimal(planned_labor);x.variance_overhead=Decimal(actual_overhead)-Decimal(planned_overhead);return x
mrp_service=MRPService()
