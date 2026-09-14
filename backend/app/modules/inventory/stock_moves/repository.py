from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.inventory.stock_moves.models import InventoryStockMove


class InventoryStockMoveRepository:
    def list(self, db: Session, company_id: int, item_id: int | None = None, variant_id: int | None = None):
        stmt = select(InventoryStockMove).where(InventoryStockMove.company_id == company_id)
        if item_id is not None:
            stmt = stmt.where(InventoryStockMove.item_id == item_id)
        stmt = stmt.where(InventoryStockMove.variant_id == variant_id) if variant_id is not None else stmt
        return list(db.scalars(stmt.order_by(InventoryStockMove.id.desc())).all())

    def get(self, db: Session, company_id: int, move_id: int):
        return db.scalar(select(InventoryStockMove).where(InventoryStockMove.company_id == company_id, InventoryStockMove.id == move_id))


inventory_stock_move_repository = InventoryStockMoveRepository()
