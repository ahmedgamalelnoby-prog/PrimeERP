from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.inventory.items.models import InventoryItem, InventoryStock
from app.modules.inventory.locations.models import InventoryLocation
from app.modules.inventory.stock_moves.location_stock import InventoryLocationStock
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

    def post(self, db: Session, *, company_id: int, move_id: int):
        move = db.scalar(
            select(InventoryStockMove).where(
                InventoryStockMove.id == move_id,
                InventoryStockMove.company_id == company_id,
            ).with_for_update()
        )
        if move is None:
            raise ValueError("Stock move not found")
        if move.status != "draft":
            raise ValueError("Only draft stock moves can be posted")

        source_balance = self._location_balance(
            db, company_id, move.item_id, move.source_location_id, lock=True
        ) if move.source_location_id else None
        destination_balance = self._location_balance(
            db, company_id, move.item_id, move.destination_location_id, lock=True
        ) if move.destination_location_id else None

        unit_cost = Decimal(move.unit_cost or 0)
        if move.source_location_id:
            if source_balance.quantity_on_hand < move.quantity:
                raise ValueError("Insufficient stock at source location")
            source_warehouse_id = source_balance.location.warehouse_id
            warehouse_source = self._warehouse_stock(db, company_id, move.item_id, source_warehouse_id)
            if unit_cost == 0:
                unit_cost = Decimal(warehouse_source.average_cost or 0)
            source_balance.quantity_on_hand -= move.quantity
            warehouse_source.quantity_on_hand -= move.quantity

        if move.destination_location_id:
            destination_warehouse_id = destination_balance.location.warehouse_id
            warehouse_destination = self._warehouse_stock(db, company_id, move.item_id, destination_warehouse_id)
            old_qty = Decimal(warehouse_destination.quantity_on_hand or 0)
            old_cost = Decimal(warehouse_destination.average_cost or 0)
            if unit_cost == 0 and old_qty > 0:
                unit_cost = old_cost
            destination_balance.quantity_on_hand += move.quantity
            warehouse_destination.quantity_on_hand += move.quantity
            if old_qty + move.quantity > 0:
                warehouse_destination.average_cost = (
                    (old_qty * old_cost) + (Decimal(move.quantity) * unit_cost)
                ) / (old_qty + Decimal(move.quantity))

        move.unit_cost = unit_cost
        move.status = "posted"
        db.flush()
        return move

    @staticmethod
    def _location_balance(db: Session, company_id: int, item_id: int, location_id: int, *, lock: bool):
        stmt = select(InventoryLocationStock).where(
            InventoryLocationStock.company_id == company_id,
            InventoryLocationStock.item_id == item_id,
            InventoryLocationStock.location_id == location_id,
        )
        if lock:
            stmt = stmt.with_for_update()
        balance = db.scalar(stmt)
        if balance is None:
            location = db.scalar(select(InventoryLocation).where(InventoryLocation.id == location_id))
            if location is None:
                raise ValueError("Location not found")
            balance = InventoryLocationStock(
                company_id=company_id,
                item_id=item_id,
                location_id=location_id,
                quantity_on_hand=0,
                quantity_reserved=0,
            )
            db.add(balance)
            db.flush()
        return balance

    @staticmethod
    def _warehouse_stock(db: Session, company_id: int, item_id: int, warehouse_id: int):
        stock = db.scalar(
            select(InventoryStock).where(
                InventoryStock.company_id == company_id,
                InventoryStock.item_id == item_id,
                InventoryStock.warehouse_id == warehouse_id,
            ).with_for_update()
        )
        if stock is None:
            stock = InventoryStock(
                company_id=company_id,
                item_id=item_id,
                warehouse_id=warehouse_id,
                quantity_on_hand=0,
                quantity_reserved=0,
                average_cost=0,
            )
            db.add(stock)
            db.flush()
        return stock


inventory_stock_move_service = InventoryStockMoveService()
