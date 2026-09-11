from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.inventory.items.models import InventoryItem
from app.modules.inventory.locations.models import InventoryLocation
from app.modules.inventory.stock_moves.location_stock import InventoryLocationStock
from app.modules.inventory.reservations.models import InventoryReservation


class InventoryReservationService:
    def list(self, db: Session, company_id: int, item_id: int | None = None, location_id: int | None = None):
        stmt = select(InventoryReservation).where(InventoryReservation.company_id == company_id)
        if item_id:
            stmt = stmt.where(InventoryReservation.item_id == item_id)
        if location_id:
            stmt = stmt.where(InventoryReservation.location_id == location_id)
        return list(db.scalars(stmt.order_by(InventoryReservation.id.desc())).all())

    def reserve(self, db: Session, payload):
        item = db.scalar(select(InventoryItem).where(
            InventoryItem.id == payload.item_id,
            InventoryItem.company_id == payload.company_id,
            InventoryItem.is_active.is_(True),
            InventoryItem.item_type.in_(["stockable", "consumable"]),
        ))
        if item is None:
            raise ValueError("Item does not belong to the company, is inactive, or is not stockable")

        location = db.scalar(select(InventoryLocation).where(
            InventoryLocation.id == payload.location_id,
            InventoryLocation.company_id == payload.company_id,
            InventoryLocation.is_active.is_(True),
        ))
        if location is None:
            raise ValueError("Location does not belong to the company or is inactive")
        if location.is_virtual:
            raise ValueError("Virtual locations cannot hold reservations")

        balance = self._locked_balance(db, payload.company_id, payload.item_id, payload.location_id)
        available = balance.quantity_on_hand - balance.quantity_reserved
        if available < payload.quantity:
            raise ValueError(f"Insufficient available stock: {available}")

        balance.quantity_reserved += payload.quantity
        reservation = InventoryReservation(**payload.model_dump(), status="active")
        db.add(reservation)
        db.flush()
        return reservation

    def release(self, db: Session, *, company_id: int, reservation_id: int):
        reservation = self._locked_reservation(db, company_id, reservation_id)
        if reservation.status != "active":
            raise ValueError("Only active reservations can be released")
        balance = self._locked_balance(db, company_id, reservation.item_id, reservation.location_id)
        if balance.quantity_reserved < reservation.quantity:
            raise ValueError("Reservation balance is inconsistent")
        balance.quantity_reserved -= reservation.quantity
        reservation.status = "released"
        db.flush()
        return reservation

    def consume(self, db: Session, *, company_id: int, reservation_id: int):
        reservation = self._locked_reservation(db, company_id, reservation_id)
        if reservation.status != "active":
            raise ValueError("Only active reservations can be consumed")
        balance = self._locked_balance(db, company_id, reservation.item_id, reservation.location_id)
        if balance.quantity_reserved < reservation.quantity:
            raise ValueError("Reservation balance is inconsistent")
        balance.quantity_reserved -= reservation.quantity
        reservation.status = "consumed"
        db.flush()
        return reservation

    def cancel(self, db: Session, *, company_id: int, reservation_id: int):
        reservation = self._locked_reservation(db, company_id, reservation_id)
        if reservation.status != "active":
            raise ValueError("Only active reservations can be cancelled")
        balance = self._locked_balance(db, company_id, reservation.item_id, reservation.location_id)
        if balance.quantity_reserved < reservation.quantity:
            raise ValueError("Reservation balance is inconsistent")
        balance.quantity_reserved -= reservation.quantity
        reservation.status = "cancelled"
        db.flush()
        return reservation

    @staticmethod
    def _locked_reservation(db: Session, company_id: int, reservation_id: int):
        reservation = db.scalar(select(InventoryReservation).where(
            InventoryReservation.id == reservation_id,
            InventoryReservation.company_id == company_id,
        ).with_for_update())
        if reservation is None:
            raise ValueError("Reservation not found")
        return reservation

    @staticmethod
    def _locked_balance(db: Session, company_id: int, item_id: int, location_id: int):
        balance = db.scalar(select(InventoryLocationStock).where(
            InventoryLocationStock.company_id == company_id,
            InventoryLocationStock.item_id == item_id,
            InventoryLocationStock.location_id == location_id,
        ).with_for_update())
        if balance is None:
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


inventory_reservation_service = InventoryReservationService()
