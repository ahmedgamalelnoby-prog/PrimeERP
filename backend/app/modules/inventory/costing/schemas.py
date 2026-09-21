from decimal import Decimal

from pydantic import BaseModel


class InventoryValuationRow(BaseModel):
    item_id: int
    variant_id: int | None = None
    warehouse_id: int
    quantity_on_hand: Decimal
    average_cost: Decimal
    inventory_value: Decimal


class InventoryValuationResponse(BaseModel):
    company_id: int
    rows: list[InventoryValuationRow]
    total_value: Decimal
