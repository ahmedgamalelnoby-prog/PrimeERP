from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.catalog.models import ProductVariant
from app.modules.inventory.items.models import InventoryItem
from app.modules.inventory.locations.models import InventoryLocation
from app.modules.inventory.stock_moves.schemas import StockMoveCreate
from app.modules.inventory.stock_moves.service import inventory_stock_move_service
from app.modules.inventory.adjustments.models import InventoryAdjustment\nfrom app.modules.companies.models import Company


class InventoryAdjustmentService:
    def list(self, db: Session, *, company_id: int, status: str | None = None):
        stmt = select(InventoryAdjustment).where(InventoryAdjustment.company_id == company_id)
        if status:
            stmt = stmt.where(InventoryAdjustment.status == status)
        return list(db.scalars(stmt.order_by(InventoryAdjustment.id.desc())))

    def create(self, db: Session, payload):
        if payload.direction not in {"increase", "decrease"}:
            raise ValueError("Direction must be increase or decrease")
        item = db.scalar(select(InventoryItem).where(InventoryItem.id == payload.item_id, InventoryItem.company_id == payload.company_id, InventoryItem.is_active.is_(True)))
        if item is None or item.item_type not in {"stockable", "consumable"}:
            raise ValueError("Item is invalid for inventory adjustment")
        if payload.variant_id is not None:
            variant = db.scalar(select(ProductVariant).where(ProductVariant.id == payload.variant_id, ProductVariant.company_id == payload.company_id, ProductVariant.product_id == item.id, ProductVariant.active.is_(True)))
            if variant is None:
                raise ValueError("Variant does not belong to the item/company or is inactive")
        location = db.scalar(select(InventoryLocation).where(InventoryLocation.id == payload.location_id, InventoryLocation.company_id == payload.company_id, InventoryLocation.is_active.is_(True)))
        if location is None:
            raise ValueError("Location is invalid for this company")
        adjustment = InventoryAdjustment(company_id=payload.company_id, item_id=payload.item_id, variant_id=payload.variant_id, location_id=payload.location_id, quantity=payload.quantity, direction=payload.direction, unit_cost=payload.unit_cost, reason=payload.reason.strip(), reference=payload.reference, notes=payload.notes, status="draft")
        db.add(adjustment)
        db.flush()
        return adjustment

    def approve(self, db: Session, *, company_id: int, adjustment_id: int):
        adjustment = self._locked(db, company_id, adjustment_id)
        if adjustment.status != "draft":
            raise ValueError("Only draft adjustments can be approved")
        adjustment.status = "approved"
        db.flush()
        return adjustment

    def post(self, db: Session, *, tenant_id: int, company_id: int, adjustment_id: int, user_id: int):
        adjustment = self._locked(db, company_id, adjustment_id)
        if adjustment.status != "approved":
            raise ValueError("Only approved adjustments can be posted")
        source_location_id = adjustment.location_id if adjustment.direction == "decrease" else None
        destination_location_id = adjustment.location_id if adjustment.direction == "increase" else None
        move = inventory_stock_move_service.create_draft(db, StockMoveCreate(company_id=company_id, item_id=adjustment.item_id, variant_id=adjustment.variant_id, source_location_id=source_location_id, destination_location_id=destination_location_id, quantity=Decimal(adjustment.quantity), unit_cost=Decimal(adjustment.unit_cost or 0), movement_type="adjustment", reference=adjustment.reference or f"ADJ-{adjustment.id}", source_module="inventory/adjustments", source_entity="inventory_adjustment", source_id=str(adjustment.id), notes=adjustment.reason))
        inventory_stock_move_service.post(db, tenant_id=tenant_id, company_id=company_id, move_id=move.id, user_id=user_id)
        adjustment.status = "posted"
        db.flush()
        return adjustment

    def cancel(self, db: Session, *, company_id: int, adjustment_id: int):
        adjustment = self._locked(db, company_id, adjustment_id)
        if adjustment.status not in {"draft", "approved"}:
            raise ValueError("Only unposted adjustments can be cancelled")
        adjustment.status = "cancelled"
        db.flush()
        return adjustment

    @staticmethod
    def _locked(db: Session, company_id: int, adjustment_id: int):
        adjustment = db.scalar(select(InventoryAdjustment).where(InventoryAdjustment.id == adjustment_id, InventoryAdjustment.company_id == company_id).with_for_update())
        if adjustment is None:
            raise ValueError("Adjustment not found")
        return adjustment


inventory_adjustment_service = InventoryAdjustmentService()
