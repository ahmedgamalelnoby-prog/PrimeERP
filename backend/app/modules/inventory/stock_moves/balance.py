from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.inventory.items.models import InventoryItem
from app.modules.inventory.locations.models import InventoryLocation


class StockBalance:
    """Small domain service for warehouse/location stock mutations.

    The current inventory model stores the authoritative quantity at warehouse
    level. Location validation is enforced here so the ledger cannot move stock
    between companies or unrelated warehouses. A later location-balance slice
    can replace the two mutation helpers without changing the posting contract.
    """

    def __init__(self, db: Session):
        self.db = db

    def location(self, location_id: int, company_id: int) -> InventoryLocation:
        location = self.db.scalar(
            select(InventoryLocation).where(
                InventoryLocation.id == location_id,
                InventoryLocation.company_id == company_id,
            )
        )
        if location is None:
            raise ValueError("Location does not belong to the company")
        if not location.is_active:
            raise ValueError("Location is inactive")
        return location

    def item(self, item_id: int, company_id: int) -> InventoryItem:
        item = self.db.scalar(
            select(InventoryItem).where(
                InventoryItem.id == item_id,
                InventoryItem.company_id == company_id,
            )
        )
        if item is None or not item.is_active:
            raise ValueError("Item does not belong to the company or is inactive")
        if item.item_type not in {"stockable", "consumable"}:
            raise ValueError("Only stockable or consumable items can have stock movements")
        return item

    def warehouse_id(self, location: InventoryLocation) -> int:
        return int(location.warehouse_id)

    @staticmethod
    def ensure_non_negative(quantity: Decimal, amount: Decimal) -> Decimal:
        result = quantity + amount
        if result < 0:
            raise ValueError("Insufficient stock")
        return result
