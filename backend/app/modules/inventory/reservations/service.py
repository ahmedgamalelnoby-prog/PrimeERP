from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.catalog.models import ProductVariant
from app.modules.inventory.items.models import InventoryItem, InventoryStock
from app.modules.inventory.locations.models import InventoryLocation
from app.modules.inventory.stock_moves.location_stock import InventoryLocationStock
from app.modules.inventory.reservations.models import InventoryReservation, InventoryReservationConsumption


class InventoryReservationService:
    def list(self, db: Session, company_id: int, item_id: int | None = None, location_id: int | None = None, variant_id: int | None = None):
        stmt = select(InventoryReservation).where(InventoryReservation.company_id == company_id)
        if item_id:
            stmt = stmt.where(InventoryReservation.item_id == item_id)
        if location_id:
            stmt = stmt.where(InventoryReservation.location_id == location_id)
        if variant_id is not None:
            stmt = stmt.where(InventoryReservation.variant_id == variant_id)
        return list(db.scalars(stmt.order_by(InventoryReservation.id.desc())).all())

    @staticmethod
    def _validate_variant(db: Session, *, company_id: int, item: InventoryItem, variant_id: int | None):
        active_variant_id = db.scalar(select(ProductVariant.id).where(ProductVariant.company_id == company_id, ProductVariant.product_id == item.id, ProductVariant.is_active.is_(True)).limit(1))
        if variant_id is None:
            if active_variant_id is not None:
                raise ValueError("This item has active variants; reservations must identify the variant")
            return None
        variant = db.scalar(select(ProductVariant).where(ProductVariant.id == variant_id, ProductVariant.company_id == company_id, ProductVariant.product_id == item.id, ProductVariant.is_active.is_(True)))
        if variant is None:
            raise ValueError("Variant does not belong to the item/company or is inactive")
        return variant

    def reserve(self, db: Session, payload):
        item = db.scalar(select(InventoryItem).where(InventoryItem.id == payload.item_id, InventoryItem.company_id == payload.company_id, InventoryItem.is_active.is_(True), InventoryItem.item_type.in_(["stockable", "consumable"])))
        if item is None:
            raise ValueError("Item does not belong to the company, is inactive, or is not stockable")
        self._validate_variant(db, company_id=payload.company_id, item=item, variant_id=payload.variant_id)
        location = db.scalar(select(InventoryLocation).where(InventoryLocation.id == payload.location_id, InventoryLocation.company_id == payload.company_id, InventoryLocation.is_active.is_(True)))
        if location is None or location.is_virtual:
            raise ValueError("Location does not belong to the company, is inactive, or is virtual")
        balance = self._locked_balance(db, payload.company_id, payload.item_id, payload.variant_id, payload.location_id)
        warehouse_stock = self._locked_warehouse_stock(db, payload.company_id, payload.item_id, payload.variant_id, location.warehouse_id)
        available = min(balance.quantity_on_hand - balance.quantity_reserved, warehouse_stock.quantity_on_hand - warehouse_stock.quantity_reserved)
        if available < payload.quantity:
            raise ValueError(f"Insufficient available stock: {available}")
        balance.quantity_reserved += payload.quantity
        warehouse_stock.quantity_reserved += payload.quantity
        reservation = InventoryReservation(**payload.model_dump(), status="active", consumed_quantity=0)
        db.add(reservation)
        db.flush()
        return reservation

    def release(self, db: Session, *, company_id: int, reservation_id: int):
        reservation = self._locked_reservation(db, company_id, reservation_id)
        if reservation.status != "active":
            raise ValueError("Only active reservations can be released")
        remaining = Decimal(reservation.quantity) - Decimal(reservation.consumed_quantity)
        self._decrease_reserved(self._locked_balance(db, company_id, reservation.item_id, reservation.variant_id, reservation.location_id), self._locked_warehouse_stock_for_location(db, company_id, reservation.item_id, reservation.variant_id, reservation.location_id), remaining)
        reservation.status = "released"
        db.flush()
        return reservation

    def consume(self, db: Session, *, company_id: int, reservation_id: int, quantity: Decimal | None = None, source_module: str = "inventory", source_entity: str = "reservation", source_id: str | None = None):
        reservation = self._locked_reservation(db, company_id, reservation_id)
        if reservation.status != "active":
            raise ValueError("Only active reservations can be consumed")
        remaining = Decimal(reservation.quantity) - Decimal(reservation.consumed_quantity)
        consume_qty = remaining if quantity is None else Decimal(quantity)
        if consume_qty <= 0 or consume_qty > remaining:
            raise ValueError(f"Consumption quantity must be between 0 and {remaining}")
        source_id = source_id or f"consume:{reservation.id}:{consume_qty}"
        existing = db.scalar(select(InventoryReservationConsumption).where(
            InventoryReservationConsumption.company_id == company_id,
            InventoryReservationConsumption.reservation_id == reservation.id,
            InventoryReservationConsumption.source_module == source_module,
            InventoryReservationConsumption.source_entity == source_entity,
            InventoryReservationConsumption.source_id == source_id,
        ))
        if existing:
            return reservation
        balance = self._locked_balance(db, company_id, reservation.item_id, reservation.variant_id, reservation.location_id)
        warehouse = self._locked_warehouse_stock_for_location(db, company_id, reservation.item_id, reservation.variant_id, reservation.location_id)
        self._decrease_reserved(balance, warehouse, consume_qty)
        reservation.consumed_quantity = Decimal(reservation.consumed_quantity) + consume_qty
        if reservation.consumed_quantity == reservation.quantity:
            reservation.status = "consumed"
        db.add(InventoryReservationConsumption(company_id=company_id, reservation_id=reservation.id, quantity=consume_qty, source_module=source_module, source_entity=source_entity, source_id=source_id))
        db.flush()
        return reservation

    def cancel(self, db: Session, *, company_id: int, reservation_id: int):
        reservation = self._locked_reservation(db, company_id, reservation_id)
        if reservation.status != "active":
            raise ValueError("Only active reservations can be cancelled")
        remaining = Decimal(reservation.quantity) - Decimal(reservation.consumed_quantity)
        self._decrease_reserved(self._locked_balance(db, company_id, reservation.item_id, reservation.variant_id, reservation.location_id), self._locked_warehouse_stock_for_location(db, company_id, reservation.item_id, reservation.variant_id, reservation.location_id), remaining)
        reservation.status = "cancelled"
        db.flush()
        return reservation

    @staticmethod
    def _decrease_reserved(balance, warehouse_stock, quantity):
        if balance.quantity_reserved < quantity or warehouse_stock.quantity_reserved < quantity:
            raise ValueError("Reservation balance is inconsistent")
        balance.quantity_reserved -= quantity
        warehouse_stock.quantity_reserved -= quantity

    @staticmethod
    def _locked_reservation(db: Session, company_id: int, reservation_id: int):
        reservation = db.scalar(select(InventoryReservation).where(InventoryReservation.id == reservation_id, InventoryReservation.company_id == company_id).with_for_update())
        if reservation is None:
            raise ValueError("Reservation not found")
        return reservation

    @staticmethod
    def _locked_balance(db: Session, company_id: int, item_id: int, variant_id: int | None, location_id: int):
        stmt = select(InventoryLocationStock).where(InventoryLocationStock.company_id == company_id, InventoryLocationStock.item_id == item_id, InventoryLocationStock.location_id == location_id)
        stmt = stmt.where(InventoryLocationStock.variant_id == variant_id) if variant_id is not None else stmt.where(InventoryLocationStock.variant_id.is_(None))
        balance = db.scalar(stmt.with_for_update())
        if balance is None:
            balance = InventoryLocationStock(company_id=company_id, item_id=item_id, variant_id=variant_id, location_id=location_id, quantity_on_hand=0, quantity_reserved=0)
            db.add(balance); db.flush()
        return balance

    @staticmethod
    def _locked_warehouse_stock(db: Session, company_id: int, item_id: int, variant_id: int | None, warehouse_id: int):
        stmt = select(InventoryStock).where(InventoryStock.company_id == company_id, InventoryStock.item_id == item_id, InventoryStock.warehouse_id == warehouse_id)
        stmt = stmt.where(InventoryStock.variant_id == variant_id) if variant_id is not None else stmt.where(InventoryStock.variant_id.is_(None))
        stock = db.scalar(stmt.with_for_update())
        if stock is None:
            stock = InventoryStock(company_id=company_id, item_id=item_id, variant_id=variant_id, warehouse_id=warehouse_id, quantity_on_hand=0, quantity_reserved=0, average_cost=0)
            db.add(stock); db.flush()
        return stock

    def _locked_warehouse_stock_for_location(self, db: Session, company_id: int, item_id: int, variant_id: int | None, location_id: int):
        location = db.scalar(select(InventoryLocation).where(InventoryLocation.id == location_id, InventoryLocation.company_id == company_id))
        if location is None:
            raise ValueError("Location not found")
        return self._locked_warehouse_stock(db, company_id, item_id, variant_id, location.warehouse_id)


inventory_reservation_service = InventoryReservationService()
