from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.inventory.items.models import InventoryItem
from app.modules.inventory.locations.models import InventoryLocation
from app.modules.inventory.stock_moves.schemas import StockMoveCreate
from app.modules.inventory.stock_moves.service import inventory_stock_move_service
from app.modules.inventory.adjustments.models import InventoryAdjustment


class InventoryAdjustmentService:
    def list(self, db: Session, *, company_id: int, status: str | None = None):
        stmt = select(InventoryAdjustment).where(InventoryAdjustment.company_id == company_id)
        if status:
            stmt = stmt.where(InventoryAdjustment.status == status)
        return list(db.scalars(stmt.order_by(InventoryAdjustment.id.desc())))

    def create(self, db: Session, payload):
        if payload.direction not in {"increase", "decrease"}:
            raise ValueError("Direction must be increase or decrease")
        item = db.scalar(select(InventoryItem).where(
            InventoryItem.id == payload.item_id,
            InventoryItem.company_id == payload.company_id,
            InventoryItem.is_active.is_(True),
        ))
        if item is None or item.item_type not in {"stockable", "consumable"}:
            raise ValueError("Item is invalid for inventory adjustment")
        location = db.scalar(select(InventoryLocation).where(
            InventoryLocation.id == payload.location_id,
            InventoryLocation.company_id == payload.company_id,
            InventoryLocation.is_active.is_(True),
        ))
        if location is None:
            raise ValueError("Location is invalid for this company")
        adjustment = InventoryAdjustment(
            company_id=payload.company_id,
            item_id=payload.item_id,
            location_id=payload.location_id,
            quantity=payload.quantity,
            direction=payload.direction,
            unit_cost=payload.unit_cost,
            reason=payload.reason.strip(),
            reference=payload.reference,
            notes=payload.notes,
            status="draft",
        )
        db.add(adjustment)
        db.flush()
        return adjustment

    def approve(self, db: Session, *, company_id: int, adjustment_id: int):
        adjustment = self._locked(db, company_id, adjustment_id)
        if adjustment is None:
            raise ValueError("Adjustment not found")
        if adjustment.status != "draft":
            raise ValueError("Only draft adjustments can be approved")
        adjustment.status = "approved"
        db.flush()
        return adjustment

    def post(self, db: Session, *, company_id: int, adjustment_id: int):
        adjustment = self._locked(db, company_id, adjustment_id)
        if adjustment is None:
            raise ValueError("Adjustment not found")
        if adjustment.status != "approved":
            raise ValueError("Only approved adjustments can be posted")

        if adjustment.direction == "increase":
            source_location_id = None
            destination_location_id = adjustment.location_id
        else:
            source_location_id = adjustment.location_id
            destination_location_id = None

        move = inventory_stock_move_service.create_draft(
            db,
            StockMoveCreate(
                company_id=company_id,
                item_id=adjustment.item_id,
                source_location_id=source_location_id,
                destination_location_id=destination_location_id,
                quantity=Decimal(adjustment.quantity),
                unit_cost=Decimal(adjustment.unit_cost or 0),
                movement_type="adjustment",
                reference=adjustment.reference or f"ADJ-{adjustment.id}",
                source_module="inventory/adjustments",
                source_entity="inventory_adjustment",
                source_id=str(adjustment.id),
                notes=adjustment.reason,
            ),
        )
        inventory_stock_move_service.post(db, company_id=company_id, move_id=move.id)
        adjustment.status = "posted"
        db.flush()
        return adjustment

    def cancel(self, db: Session, *, company_id: int, adjustment_id: int):
        adjustment = self._locked(db, company_id, adjustment_id)
        if adjustment is None:
            raise ValueError("Adjustment not found")
        if adjustment.status not in {"draft", "approved"}:
            raise ValueError("Only unposted adjustments can be cancelled")
        adjustment.status = "cancelled"
        db.flush()
        return adjustment

    @staticmethod
    def _locked(db: Session, company_id: int, adjustment_id: int):
        return db.scalar(select(InventoryAdjustment).where(
            InventoryAdjustment.id == adjustment_id,
            InventoryAdjustment.company_id == company_id,
        ).with_for_update())


inventory_adjustment_service = InventoryAdjustmentService()
