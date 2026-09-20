from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.modules.inventory.stock_moves.models import InventoryCostLayer
class CostingEngine:
 def add_layer(self,db,**kw):
  x=InventoryCostLayer(**kw);db.add(x);db.flush();return x
 def fifo_cost(self,db,company_id,item_id,warehouse_id,quantity):
  remaining=Decimal(str(quantity));total=Decimal("0")
  rows=db.scalars(select(InventoryCostLayer).where(InventoryCostLayer.company_id==company_id,InventoryCostLayer.item_id==item_id,InventoryCostLayer.warehouse_id==warehouse_id).order_by(InventoryCostLayer.layer_date,InventoryCostLayer.id)).all()
  for x in rows:
   available=Decimal(x.quantity_in or 0)-Decimal(x.quantity_out or 0)
   take=min(available,remaining)
   if take>0: total+=take*Decimal(x.unit_cost);remaining-=take
   if remaining<=0:break
  if remaining>0: raise ValueError("Insufficient cost layers for FIFO valuation")
  return total
 def weighted_average(self,layers):
  qty=sum((Decimal(x.quantity_in or 0)-Decimal(x.quantity_out or 0) for x in layers),Decimal("0"));value=sum(((Decimal(x.quantity_in or 0)-Decimal(x.quantity_out or 0))*Decimal(x.unit_cost) for x in layers),Decimal("0"));return value/qty if qty else Decimal("0")
costing_engine=CostingEngine()
