from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.catalog.models import ProductVariant
from app.modules.inventory.items.models import InventoryItem, InventoryStock
from app.modules.inventory.locations.models import InventoryLocation
from app.modules.inventory.stock_moves.location_stock import InventoryLocationStock
from app.modules.inventory.stock_moves.models import InventoryCostLayer, InventoryStockMove
from app.modules.inventory.stock_moves.repository import inventory_stock_move_repository


class InventoryStockMoveService:
    def list(self, db: Session, company_id: int, item_id: int | None = None, variant_id: int | None = None):
        return inventory_stock_move_repository.list(db, company_id, item_id, variant_id)

    @staticmethod
    def _validate_variant(db: Session, *, company_id: int, item: InventoryItem, variant_id: int | None):
        item_id = getattr(item, "id", None)
        active_variants = db.scalar(select(ProductVariant.id).where(ProductVariant.company_id == company_id, ProductVariant.product_id == item_id, ProductVariant.is_active.is_(True)).limit(1))
        if not isinstance(active_variants, int):
            active_variants = None
        if variant_id is None:
            if active_variants is not None:
                raise ValueError("This item has active variants; stock movements must identify the variant")
            return None
        variant = db.scalar(select(ProductVariant).where(ProductVariant.id == variant_id, ProductVariant.company_id == company_id, ProductVariant.product_id == item_id, ProductVariant.is_active.is_(True)))
        if variant is None:
            raise ValueError("Variant does not belong to the item/company or is inactive")
        return variant

    def create_draft(self, db: Session, payload):
        item = db.scalar(select(InventoryItem).where(InventoryItem.id == payload.item_id, InventoryItem.company_id == payload.company_id, InventoryItem.is_active.is_(True)))
        if item is None:
            raise ValueError("Item does not belong to the company or is inactive")
        if item.item_type not in {"stockable", "consumable"}:
            raise ValueError("Only stockable or consumable items can have stock movements")
        self._validate_variant(db, company_id=payload.company_id, item=item, variant_id=payload.variant_id)
        locations = {}
        for location_id in (payload.source_location_id, payload.destination_location_id):
            if location_id is not None:
                location = db.scalar(select(InventoryLocation).where(InventoryLocation.id == location_id, InventoryLocation.company_id == payload.company_id, InventoryLocation.is_active.is_(True)))
                if location is None:
                    raise ValueError("Location does not belong to the company or is inactive")
                locations[location_id] = location
        if payload.source_location_id is None and payload.destination_location_id is None:
            raise ValueError("At least one stock location is required")
        if payload.movement_type in {"issue", "transfer", "return"} and payload.source_location_id is None:
            raise ValueError("Source location is required for this movement")
        if payload.movement_type in {"receipt", "transfer", "return"} and payload.destination_location_id is None:
            raise ValueError("Destination location is required for this movement")
        if payload.source_location_id and payload.destination_location_id and payload.source_location_id == payload.destination_location_id:
            raise ValueError("Source and destination locations must differ")
        if payload.movement_type == "transfer":
            source = locations[payload.source_location_id]
            destination = locations[payload.destination_location_id]
            if source.warehouse_id == destination.warehouse_id:
                raise ValueError("Use a direct stock move for an intra-warehouse location transfer")
        move = InventoryStockMove(**payload.model_dump(), status="draft")
        db.add(move)
        db.flush()
        return move

    def post(self, db: Session, *, company_id: int, move_id: int):
        move = db.scalar(select(InventoryStockMove).where(InventoryStockMove.id == move_id, InventoryStockMove.company_id == company_id).with_for_update())
        if move is None:
            raise ValueError("Stock move not found")
        if move.status != "draft":
            raise ValueError("Only draft stock moves can be posted")
        source_entity = getattr(move, "source_entity", None)
        if source_entity == "sales_delivery" and move.movement_type != "issue":
            raise ValueError("Sales delivery stock moves must be issue movements")
        item = db.scalar(select(InventoryItem).where(InventoryItem.id == move.item_id, InventoryItem.company_id == company_id, InventoryItem.is_active.is_(True)))
        if item is None:
            raise ValueError("Item is unavailable for posting")
        self._validate_variant(db, company_id=company_id, item=item, variant_id=getattr(move, "variant_id", None))
        variant_id = getattr(move, "variant_id", None)
        source_balance = self._location_balance(db, company_id, move.item_id, variant_id, move.source_location_id, lock=True) if move.source_location_id else None
        destination_balance = self._location_balance(db, company_id, move.item_id, variant_id, move.destination_location_id, lock=True) if move.destination_location_id else None
        source_warehouse_id = source_balance.location.warehouse_id if source_balance else None
        destination_warehouse_id = destination_balance.location.warehouse_id if destination_balance else None
        unit_cost = Decimal(move.unit_cost or 0)
        fifo_allocations: list[tuple[Decimal, Decimal]] = []

        if source_balance:
            quantity = Decimal(move.quantity)
            on_hand = Decimal(source_balance.quantity_on_hand or 0)
            reserved = Decimal(source_balance.quantity_reserved or 0)
            if move.movement_type in {"issue", "transfer", "adjustment"} and on_hand - reserved < quantity:
                raise ValueError("Insufficient available stock after excluding reserved quantity")
            if on_hand < quantity:
                raise ValueError("Insufficient stock at source location")
            warehouse_source = self._warehouse_stock(db, company_id, move.item_id, variant_id, source_warehouse_id)
            if move.movement_type in {"issue", "transfer", "adjustment"} and Decimal(warehouse_source.quantity_on_hand or 0) - Decimal(warehouse_source.quantity_reserved or 0) < quantity:
                raise ValueError("Insufficient available warehouse stock after excluding reserved quantity")
            if item.costing_method == "fifo":
                fifo_allocations = self._consume_fifo_layers(db, company_id, move.item_id, variant_id, source_warehouse_id, quantity)
                unit_cost = self._weighted_cost(fifo_allocations)
            elif unit_cost == 0:
                unit_cost = Decimal(item.standard_cost or item.purchase_price or 0) if item.costing_method == "standard" else Decimal(warehouse_source.average_cost or 0)
            source_balance.quantity_on_hand -= quantity
            warehouse_source.quantity_on_hand -= quantity

        if destination_balance:
            quantity = Decimal(move.quantity)
            warehouse_destination = self._warehouse_stock(db, company_id, move.item_id, variant_id, destination_warehouse_id)
            old_qty = Decimal(warehouse_destination.quantity_on_hand or 0)
            old_cost = Decimal(warehouse_destination.average_cost or 0)
            if unit_cost == 0:
                unit_cost = old_cost if old_qty > 0 else Decimal(item.standard_cost or item.purchase_price or 0)
            destination_balance.quantity_on_hand += quantity
            warehouse_destination.quantity_on_hand += quantity
            new_qty = old_qty + quantity
            if new_qty > 0:
                warehouse_destination.average_cost = ((old_qty * old_cost) + (quantity * unit_cost)) / new_qty
            if item.costing_method == "fifo":
                self._add_fifo_layers(db, company_id, move.item_id, variant_id, destination_warehouse_id, move.id, fifo_allocations or [(quantity, unit_cost)])

        if item.costing_method == "fifo" and source_balance and not fifo_allocations:
            raise ValueError("FIFO valuation could not determine a cost layer")
        move.unit_cost = unit_cost
        move.status = "posted"
        db.flush()
        return move

    @staticmethod
    def _location_balance(db: Session, company_id: int, item_id: int, variant_id: int | None, location_id: int, *, lock: bool):
        stmt = select(InventoryLocationStock).where(InventoryLocationStock.company_id == company_id, InventoryLocationStock.item_id == item_id, InventoryLocationStock.location_id == location_id)
        stmt = stmt.where(InventoryLocationStock.variant_id == variant_id) if variant_id is not None else stmt.where(InventoryLocationStock.variant_id.is_(None))
        if lock:
            stmt = stmt.with_for_update()
        balance = db.scalar(stmt)
        if balance is None:
            location = db.scalar(select(InventoryLocation).where(InventoryLocation.id == location_id, InventoryLocation.company_id == company_id))
            if location is None:
                raise ValueError("Location not found")
            balance = InventoryLocationStock(company_id=company_id, item_id=item_id, variant_id=variant_id, location_id=location_id, quantity_on_hand=0, quantity_reserved=0)
            db.add(balance)
            db.flush()
        return balance

    @staticmethod
    def _warehouse_stock(db: Session, company_id: int, item_id: int, variant_id: int | None, warehouse_id: int):
        stmt = select(InventoryStock).where(InventoryStock.company_id == company_id, InventoryStock.item_id == item_id, InventoryStock.warehouse_id == warehouse_id)
        stmt = stmt.where(InventoryStock.variant_id == variant_id) if variant_id is not None else stmt.where(InventoryStock.variant_id.is_(None))
        stock = db.scalar(stmt.with_for_update())
        if stock is None:
            stock = InventoryStock(company_id=company_id, item_id=item_id, variant_id=variant_id, warehouse_id=warehouse_id, quantity_on_hand=0, quantity_reserved=0, average_cost=0)
            db.add(stock)
            db.flush()
        return stock

    def _consume_fifo_layers(self, db, company_id, item_id, variant_id, warehouse_id, quantity):
        stmt = select(InventoryCostLayer).where(InventoryCostLayer.company_id == company_id, InventoryCostLayer.item_id == item_id, InventoryCostLayer.warehouse_id == warehouse_id, InventoryCostLayer.quantity_remaining > 0)
        stmt = stmt.where(InventoryCostLayer.variant_id == variant_id) if variant_id is not None else stmt.where(InventoryCostLayer.variant_id.is_(None))
        layers = db.scalars(stmt.order_by(InventoryCostLayer.id).with_for_update()).all()
        available = sum((Decimal(layer.quantity_remaining) for layer in layers), Decimal("0"))
        if available < quantity:
            raise ValueError("FIFO cost layers are insufficient for the selected item/variant")
        remaining = quantity; allocations = []
        for layer in layers:
            if remaining <= 0: break
            take = min(remaining, Decimal(layer.quantity_remaining)); layer.quantity_remaining -= take; allocations.append((take, Decimal(layer.unit_cost))); remaining -= take
        return allocations

    @staticmethod
    def _weighted_cost(allocations):
        quantity = sum((qty for qty, _ in allocations), Decimal("0"))
        return Decimal("0") if quantity <= 0 else sum((qty * cost for qty, cost in allocations), Decimal("0")) / quantity

    @staticmethod
    def _add_fifo_layers(db, company_id, item_id, variant_id, warehouse_id, move_id, allocations):
        for quantity, unit_cost in allocations:
            if quantity > 0: db.add(InventoryCostLayer(company_id=company_id, item_id=item_id, variant_id=variant_id, warehouse_id=warehouse_id, receipt_move_id=move_id, quantity_remaining=quantity, unit_cost=unit_cost))
        db.flush()


inventory_stock_move_service = InventoryStockMoveService()
