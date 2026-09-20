from decimal import Decimal
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from app.modules.inventory.costing.variance_models import InventoryCostVariance
from app.modules.inventory.items.models import InventoryStock
from app.modules.catalog.models import ProductCostHistory

class InventoryCostVarianceService:
    def calculate(self, db: Session, *, company_id:int, item_id:int, warehouse_id:int, variant_id:int|None, user_id:int, basis:str="standard_vs_actual"):
        stock=db.scalar(select(InventoryStock).where(
            InventoryStock.company_id==company_id, InventoryStock.item_id==item_id,
            InventoryStock.warehouse_id==warehouse_id,
            InventoryStock.variant_id==variant_id
        ).with_for_update())
        if stock is None: raise ValueError("Inventory stock was not found")
        qty=Decimal(stock.quantity_on_hand or 0)
        actual=Decimal(stock.average_cost or 0)
        hist=db.scalar(select(ProductCostHistory).where(
            ProductCostHistory.company_id==company_id,
            ProductCostHistory.product_id==item_id
        ).order_by(ProductCostHistory.effective_at.desc(), ProductCostHistory.id.desc()))
        standard=Decimal(hist.cost) if hist is not None else actual
        variance=(actual-standard)*qty
        row=InventoryCostVariance(company_id=company_id,item_id=item_id,warehouse_id=warehouse_id,variant_id=variant_id,
            quantity=qty,standard_unit_cost=standard,actual_unit_cost=actual,variance_value=variance,basis=basis,status="calculated",created_by=user_id)
        db.add(row); db.flush(); return row
    def list(self, db:Session, company_id:int, item_id:int|None=None):
        q=select(InventoryCostVariance).where(InventoryCostVariance.company_id==company_id)
        if item_id: q=q.where(InventoryCostVariance.item_id==item_id)
        return list(db.scalars(q.order_by(InventoryCostVariance.id.desc())).all())
inventory_cost_variance_service=InventoryCostVarianceService()
