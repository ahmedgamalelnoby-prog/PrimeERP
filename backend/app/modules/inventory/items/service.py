from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.inventory.items.models import InventoryItem
from app.modules.inventory.items.repository import inventory_item_repository
from app.modules.inventory.items.schemas import InventoryItemCreate, InventoryItemUpdate


class InventoryItemService:
    def list(self, db: Session, *, company_id: int, active_only: bool = True):
        return inventory_item_repository.list_items(
            db, company_id=company_id, active_only=active_only
        )

    def get(self, db: Session, *, company_id: int, item_id: int):
        return inventory_item_repository.get_item(
            db, company_id=company_id, item_id=item_id
        )

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

    def update(
        self,
        db: Session,
        *,
        company_id: int,
        item_id: int,
        payload: InventoryItemUpdate,
    ):
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

    def stock(self, db: Session, *, company_id: int, item_id: int | None = None):
        return inventory_item_repository.list_stock(
            db, company_id=company_id, item_id=item_id
        )


inventory_item_service = InventoryItemService()
