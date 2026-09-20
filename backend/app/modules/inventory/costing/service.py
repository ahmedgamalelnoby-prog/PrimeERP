from decimal import Decimal

from sqlalchemy import MetaData, select
from sqlalchemy.orm import Session

from app.modules.inventory.items.models import InventoryItem, InventoryStock
from app.modules.inventory.costing.schemas import InventoryValuationResponse, InventoryValuationRow


class InventoryCostingService:
    def valuation(self, db: Session, company_id: int, warehouse_id: int | None = None, item_id: int | None = None):
        stmt = (
            select(InventoryStock, InventoryItem.costing_method)
            .join(InventoryItem, InventoryItem.id == InventoryStock.item_id)
            .where(
                InventoryStock.company_id == company_id,
                InventoryItem.company_id == company_id,
            )
        )
        if warehouse_id:
            stmt = stmt.where(InventoryStock.warehouse_id == warehouse_id)
        if item_id:
            stmt = stmt.where(InventoryStock.item_id == item_id)

        # FIFO valuation must come from the remaining cost layers, not the
        # moving average stored on InventoryStock. Reflection keeps this
        # read-only reporting service independent from the optional FIFO model
        # namespace while still using the migration's canonical table.
        metadata = MetaData()
        layers = None
        try:
            metadata.reflect(bind=db.get_bind(), only=["inventory_cost_layers"])
            layers = metadata.tables.get("inventory_cost_layers")
        except Exception:
            layers = None

        rows = []
        total = Decimal("0")
        for stock, costing_method in db.execute(
            stmt.order_by(InventoryStock.item_id, InventoryStock.variant_id, InventoryStock.warehouse_id)
        ).all():
            quantity = Decimal(stock.quantity_on_hand or 0)
            average_cost = Decimal(stock.average_cost or 0)
            value = quantity * average_cost

            if costing_method == "fifo" and layers is not None:
                fifo_conditions = [
                    layers.c.company_id == company_id,
                    layers.c.item_id == stock.item_id,
                    layers.c.warehouse_id == stock.warehouse_id,
                    layers.c.quantity_remaining > 0,
                ]
                if hasattr(layers.c, "variant_id"):
                    fifo_conditions.append(
                        layers.c.variant_id == getattr(stock, "variant_id", None)
                    )
                fifo_stmt = select(
                    layers.c.quantity_remaining,
                    layers.c.unit_cost,
                ).where(*fifo_conditions)
                    layers.c.company_id == company_id,
                    layers.c.item_id == stock.item_id,
                    layers.c.warehouse_id == stock.warehouse_id,
                    layers.c.quantity_remaining > 0,
                )
                fifo_value = Decimal("0")
                fifo_quantity = Decimal("0")
                for layer_qty, layer_cost in db.execute(fifo_stmt).all():
                    qty = Decimal(layer_qty or 0)
                    cost = Decimal(layer_cost or 0)
                    fifo_quantity += qty
                    fifo_value += qty * cost
                # Layers are authoritative for FIFO when present. A zero-layer
                # legacy stock falls back to the stock average to avoid hiding
                # historical inventory that predates FIFO tracking.
                if fifo_quantity > 0:
                    quantity = fifo_quantity
                    value = fifo_value
                    average_cost = value / quantity

            rows.append(
                InventoryValuationRow(
                    item_id=stock.item_id,
                    variant_id=getattr(stock, "variant_id", None),
                    warehouse_id=stock.warehouse_id,
                    quantity_on_hand=quantity,
                    average_cost=average_cost,
                    inventory_value=value,
                )
            )
            total += value

        return InventoryValuationResponse(company_id=company_id, rows=rows, total_value=total)


inventory_costing_service = InventoryCostingService()
