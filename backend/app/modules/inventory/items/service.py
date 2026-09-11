from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.inventory.items.models import InventoryItem
from app.modules.inventory.items.schemas import InventoryItemCreate, InventoryItemUpdate


class InventoryItemService:
    def list(self, db: Session, *, company_id: int, active_only: bool = True):
        stmt = select(InventoryItem).where(InventoryItem.company_id == company_id)
        if active_only:
            stmt = stmt.where(InventoryItem.is_active.is_(True))
        return db.scalars(stmt.order_by(InventoryItem.sku)).all()

    def get(self, db: Session, *, company_id: int, item_id: int):
        return db.scalar(select(InventoryItem).where(InventoryItem.company_id == company_id, InventoryItem.id == item_id))

    def create(self, db: Session, payload: InventoryItemCreate):
        item = InventoryItem(**payload.model_dump())
        db.add(item)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise ValueError("SKU or barcode already exists for this company") from exc
        db.refresh(item)
        return item

    def update(self, db: Session, *, company_id: int, item_id: int, payload: InventoryItemUpdate):
        item = self.get(db, company_id=company_id, item_id=item_id)
        if item is None:
            raise ValueError("Inventory item not found")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(item, key, value)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise ValueError("SKU or barcode already exists for this company") from exc
        db.refresh(item)
        return item


inventory_item_service = InventoryItemService()
