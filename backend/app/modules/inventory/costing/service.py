from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.inventory.items.models import InventoryStock
from app.modules.inventory.costing.schemas import InventoryValuationResponse, InventoryValuationRow


class InventoryCostingService:
    def valuation(self, db: Session, company_id: int, warehouse_id: int | None = None, item_id: int | None = None):
        stmt = select(InventoryStock).where(InventoryStock.company_id == company_id)
        if warehouse_id:
            stmt = stmt.where(InventoryStock.warehouse_id == warehouse_id)
        if item_id:
            stmt = stmt.where(InventoryStock.item_id == item_id)

        rows = []
        total = Decimal("0")
        for stock in db.scalars(stmt.order_by(InventoryStock.item_id, InventoryStock.warehouse_id)).all():
            quantity = Decimal(stock.quantity_on_hand or 0)
            average_cost = Decimal(stock.average_cost or 0)
            value = quantity * average_cost
            rows.append(InventoryValuationRow(
                item_id=stock.item_id,
                warehouse_id=stock.warehouse_id,
                quantity_on_hand=quantity,
                average_cost=average_cost,
                inventory_value=value,
            ))
            total += value
        return InventoryValuationResponse(company_id=company_id, rows=rows, total_value=total)


inventory_costing_service = InventoryCostingService()
