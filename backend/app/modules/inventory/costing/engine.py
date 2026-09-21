from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.modules.inventory.stock_moves.models import InventoryCostLayer

class CostingEngine:
    def add_layer(self, db: Session, **kw):
        layer=InventoryCostLayer(**kw);db.add(layer);db.flush();return layer

    def fifo_cost(self, db: Session, company_id: int, item_id: int, warehouse_id: int, quantity, variant_id: int|None=None):
        remaining=Decimal(str(quantity)); total=Decimal("0")
        stmt=select(InventoryCostLayer).where(
            InventoryCostLayer.company_id==company_id,
            InventoryCostLayer.item_id==item_id,
            InventoryCostLayer.warehouse_id==warehouse_id,
            InventoryCostLayer.quantity_remaining>0,
        )
        if variant_id is None: stmt=stmt.where(InventoryCostLayer.variant_id.is_(None))
        else: stmt=stmt.where(InventoryCostLayer.variant_id==variant_id)
        for layer in db.scalars(stmt.order_by(InventoryCostLayer.id.asc()).with_for_update()).all():
            if remaining<=0: break
            available=Decimal(layer.quantity_remaining or 0)
            take=min(available,remaining)
            total+=take*Decimal(layer.unit_cost or 0)
            remaining-=take
        if remaining>0: raise ValueError("Insufficient cost layers for FIFO valuation")
        return total

    def weighted_average(self,layers):
        qty=sum((Decimal(x.quantity_remaining or 0) for x in layers),Decimal("0"))
        value=sum((Decimal(x.quantity_remaining or 0)*Decimal(x.unit_cost or 0) for x in layers),Decimal("0"))
        return value/qty if qty else Decimal("0")

costing_engine=CostingEngine()
