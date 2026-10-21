from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.inventory.items.models import InventoryItem, InventoryStock


class InventoryItemRepository:
    def list_items(self, db: Session, *, company_id: int, active_only: bool = True):
        stmt = select(InventoryItem).where(InventoryItem.company_id == company_id)
        if active_only:
            stmt = stmt.where(InventoryItem.is_active.is_(True))
        return db.scalars(stmt.order_by(InventoryItem.sku)).all()

    def get_item(self, db: Session, *, company_id: int, item_id: int):
        return db.scalar(
            select(InventoryItem).where(
                InventoryItem.company_id == company_id,
                InventoryItem.id == item_id,
            )
        )

    def list_stock(self, db: Session, *, company_id: int, item_id: int | None = None):
        stmt = select(InventoryStock).where(InventoryStock.company_id == company_id)
        if item_id is not None:
            stmt = stmt.where(InventoryStock.item_id == item_id)
        return db.scalars(stmt.order_by(InventoryStock.item_id, InventoryStock.warehouse_id)).all()


inventory_item_repository = InventoryItemRepository()
