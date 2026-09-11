from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.inventory.items.models import InventoryItem
from app.modules.inventory.locations.models import InventoryLocation
from app.modules.inventory.stock_moves.models import InventoryStockMove
from app.modules.inventory.stock_moves.repository import inventory_stock_move_repository


class InventoryStockMoveService:
    def list(self, db: Session, company_id: int, item_id: int | None = None):
        return inventory_stock_move_repository.list(db, company_id, item_id)

    def create_draft(self, db: Session, payload):
        item = db.scalar(
            select(InventoryItem).where(
                InventoryItem.id == payload.item_id,
                InventoryItem.company_id == payload.company_id,
                InventoryItem.is_active.is_(True),
            )
        )
        if item is None:
            raise ValueError("Item does not belong to the company or is inactive")

        locations = {}
        for location_id in (payload.source_location_id, payload.destination_location_id):
            if location_id is not None:
                location = db.scalar(
                    select(InventoryLocation).where(
                        InventoryLocation.id == location_id,
                        InventoryLocation.company_id == payload.company_id,
                        InventoryLocation.is_active.is_(True),
                    )
                )
                if location is None:
                    raise ValueError("Location does not belong to the company or is inactive")
                locations[location_id] = location

        if payload.source_location_id is None and payload.destination_location_id is None:
            raise ValueError("At least one stock location is required")
        if payload.movement_type in {"issue", "transfer", "return"} and payload.source_location_id is None:
            raise ValueError("Source location is required for this movement")
        if payload.movement_type in {"receipt", "transfer", "return"} and payload.destination_location_id is None:
            raise ValueError("Destination location is required for this movement")

        move = InventoryStockMove(**payload.model_dump(), status="draft")
        db.add(move)
        db.flush()
        return move


inventory_stock_move_service = InventoryStockMoveService()
