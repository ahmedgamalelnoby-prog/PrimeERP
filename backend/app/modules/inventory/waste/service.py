from datetime import datetime,timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.modules.inventory.waste.models import InventoryWaste
from app.modules.inventory.stock_moves.schemas import StockMoveCreate
from app.modules.inventory.stock_moves.service import inventory_stock_move_service
from app.modules.inventory.items.models import InventoryItem
from app.modules.inventory.locations.models import InventoryLocation
class InventoryWasteService:
 def create(self,db:Session,p,user_id:int):
  if not db.scalar(select(InventoryItem).where(InventoryItem.id==p.item_id,InventoryItem.company_id==p.company_id,InventoryItem.is_active.is_(True))):raise ValueError("Item is invalid")
  if not db.scalar(select(InventoryLocation).where(InventoryLocation.id==p.location_id,InventoryLocation.company_id==p.company_id,InventoryLocation.is_active.is_(True))):raise ValueError("Location is invalid")
  x=InventoryWaste(**p.model_dump(),status="draft",created_by=user_id);db.add(x);db.flush();return x
 def approve(self,db,company_id,waste_id):
  x=self._locked(db,company_id,waste_id)
  if x.status!="draft":raise ValueError("Only draft waste can be approved")
  x.status="approved";db.flush();return x
 def post(self,db,tenant_id,company_id,waste_id,user_id):
  x=self._locked(db,company_id,waste_id)
  if x.status!="approved":raise ValueError("Only approved waste can be posted")
  move=inventory_stock_move_service.create_draft(db,StockMoveCreate(company_id=company_id,item_id=x.item_id,variant_id=x.variant_id,source_location_id=x.location_id,quantity=x.quantity,unit_cost=x.unit_cost,movement_type="issue",reference=x.reference or f"WASTE-{x.id}",source_module="inventory/waste",source_entity="inventory_waste",source_id=str(x.id),notes=x.reason))
  inventory_stock_move_service.post(db,tenant_id=tenant_id,company_id=company_id,move_id=move.id,user_id=user_id);x.status="posted";x.posted_at=datetime.now(timezone.utc);db.flush();return x
 def _locked(self,db,company_id,waste_id):
  x=db.scalar(select(InventoryWaste).where(InventoryWaste.id==waste_id,InventoryWaste.company_id==company_id).with_for_update())
  if not x:raise ValueError("Waste record not found")
  return x
inventory_waste_service=InventoryWasteService()