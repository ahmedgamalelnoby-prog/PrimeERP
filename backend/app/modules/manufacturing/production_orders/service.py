from datetime import datetime, timezone
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP

from sqlalchemy import select, or_
from sqlalchemy.orm import Session, selectinload

from app.modules.catalog.models import Recipe, RecipeLine, ProductVariant
from app.modules.company_settings.service import get_company_setting
from app.modules.inventory.items.models import InventoryItem
from app.modules.inventory.locations.models import InventoryLocation
from app.modules.inventory.stock_moves.models import InventoryStockMove
from app.modules.inventory.stock_moves.schemas import StockMoveCreate
from app.modules.inventory.stock_moves.service import inventory_stock_move_service
from app.modules.manufacturing.production_orders.models import ManufacturingWorkOrder, ManufacturingWorkOrderLine


FOUR_PLACES = Decimal("0.0001")
EIGHT_PLACES = Decimal("0.00000001")


class ManufacturingWorkOrderService:
    @staticmethod
    def get(db: Session, *, company_id: int, work_order_id: int, lock: bool = False):
        stmt = select(ManufacturingWorkOrder).options(
            selectinload(ManufacturingWorkOrder.lines)
        ).where(
            ManufacturingWorkOrder.id == work_order_id,
            ManufacturingWorkOrder.company_id == company_id,
        )
        if lock:
            stmt = stmt.with_for_update()
        return db.scalar(stmt)

    @staticmethod
    def list(db: Session, *, company_id: int):
        return db.scalars(
            select(ManufacturingWorkOrder)
            .options(selectinload(ManufacturingWorkOrder.lines))
            .where(ManufacturingWorkOrder.company_id == company_id)
            .order_by(ManufacturingWorkOrder.id.desc())
            .limit(500)
        ).all()

    def create(self, db: Session, *, payload, user_id: int):
        normalized_number = payload.number.strip()
        if not normalized_number:
            raise ValueError("Work order number cannot be blank")
        if payload.source_location_id == payload.destination_location_id:
            raise ValueError("Production source and destination locations must differ")
        recipe = db.scalar(select(Recipe).where(
            Recipe.id == payload.recipe_id,
            Recipe.company_id == payload.company_id,
            Recipe.is_active.is_(True),
        ).options(selectinload(Recipe.lines)))
        if recipe is None:
            raise ValueError("Active recipe does not belong to the selected company")
        if not recipe.lines:
            raise ValueError("A production work order requires at least one recipe component")
        output = db.scalar(select(InventoryItem).where(
            InventoryItem.id == recipe.product_id,
            InventoryItem.company_id == payload.company_id,
            InventoryItem.is_active.is_(True),
            InventoryItem.item_type.in_(["stockable", "consumable"]),
        ))
        if output is None:
            raise ValueError("Recipe output must be an active stockable or consumable item")
        if recipe.variant_id is not None:
            variant = db.scalar(select(ProductVariant).where(
                ProductVariant.id == recipe.variant_id,
                ProductVariant.company_id == payload.company_id,
                ProductVariant.product_id == recipe.product_id,
                ProductVariant.is_active.is_(True),
            ))
            if variant is None:
                raise ValueError("Recipe output variant is unavailable")
        else:
            variant_id = db.scalar(select(ProductVariant.id).where(
                ProductVariant.company_id == payload.company_id,
                ProductVariant.product_id == recipe.product_id,
                ProductVariant.is_active.is_(True),
            ).limit(1))
            if variant_id is not None:
                raise ValueError("Recipe must identify an output variant for a variant-controlled item")

        locations = db.scalars(select(InventoryLocation).where(
            InventoryLocation.id.in_([payload.source_location_id, payload.destination_location_id]),
            InventoryLocation.company_id == payload.company_id,
            InventoryLocation.is_active.is_(True),
            InventoryLocation.is_virtual.is_(False),
        )).all()
        by_id = {location.id: location for location in locations}
        if set(by_id) != {payload.source_location_id, payload.destination_location_id}:
            raise ValueError("Production locations must be active, physical locations belonging to the company")

        order = ManufacturingWorkOrder(
            company_id=payload.company_id,
            number=normalized_number,
            recipe_id=recipe.id,
            recipe_version=recipe.version,
            output_item_id=recipe.product_id,
            output_variant_id=recipe.variant_id,
            source_location_id=payload.source_location_id,
            destination_location_id=payload.destination_location_id,
            planned_quantity=payload.planned_quantity,
            status="planned",
            created_by_user_id=user_id,
        )
        db.add(order)
        db.flush()
        for recipe_line in recipe.lines:
            ingredient_id = recipe_line.ingredient_item_id or recipe_line.ingredient_product_id
            ingredient = db.scalar(select(InventoryItem).where(
                InventoryItem.id == ingredient_id,
                InventoryItem.company_id == payload.company_id,
                InventoryItem.is_active.is_(True),
                InventoryItem.item_type.in_(["stockable", "consumable"]),
            ))
            if ingredient is None:
                raise ValueError("Every recipe component must be an active stockable or consumable company item")
            active_variant_id = db.scalar(select(ProductVariant.id).where(
                ProductVariant.company_id == payload.company_id,
                ProductVariant.product_id == ingredient_id,
                ProductVariant.is_active.is_(True),
            ).limit(1))
            if active_variant_id is not None:
                raise ValueError("Recipe components with active variants require a variant-aware recipe line")
            line_rate = (
                Decimal(recipe_line.quantity)
                * Decimal(recipe_line.conversion_factor_to_product_uom or 1)
                * (Decimal("1") + Decimal(recipe_line.waste_percentage or 0) / Decimal("100"))
                * (Decimal("1") + Decimal(recipe.waste_percentage or 0) / Decimal("100"))
                / Decimal(recipe.yield_quantity)
            ).quantize(EIGHT_PLACES, rounding=ROUND_HALF_UP)
            if line_rate <= 0:
                raise ValueError("Recipe component rate must be positive")
            db.add(ManufacturingWorkOrderLine(
                work_order_id=order.id,
                source_recipe_line_id=recipe_line.id,
                ingredient_item_id=ingredient_id,
                quantity_per_output=line_rate,
            ))
        db.flush()
        return order

    def release(self, db: Session, *, company_id: int, work_order_id: int, user_id: int):
        order = self.get(db, company_id=company_id, work_order_id=work_order_id, lock=True)
        if order is None:
            raise ValueError("Work order not found")
        if order.status != "planned":
            raise ValueError("Only planned work orders can be released")
        if not order.lines:
            raise ValueError("Work order has no recipe component snapshot")
        order.status = "released"
        order.released_by_user_id = user_id
        order.released_at = datetime.now(timezone.utc)
        db.flush()
        return order

    def complete(
        self,
        db: Session,
        *,
        tenant_id: int,
        company_id: int,
        work_order_id: int,
        produced_quantity: Decimal,
        user_id: int,
    ):
        order = self.get(db, company_id=company_id, work_order_id=work_order_id, lock=True)
        if order is None:
            raise ValueError("Work order not found")
        if order.status != "released":
            raise ValueError("Only released work orders can be completed")
        if produced_quantity > Decimal(order.planned_quantity) and get_company_setting(
            db, company_id, "manufacturing.allow_overproduction"
        ) is not True:
            raise ValueError("Produced quantity cannot exceed the planned quantity under company policy")

        total_component_value = Decimal("0")
        for line in order.lines:
            issue_quantity = (
                Decimal(line.quantity_per_output) * produced_quantity
            ).quantize(FOUR_PLACES, rounding=ROUND_CEILING)
            move = inventory_stock_move_service.create_draft(db, StockMoveCreate(
                company_id=company_id,
                item_id=line.ingredient_item_id,
                source_location_id=order.source_location_id,
                quantity=issue_quantity,
                unit_cost=0,
                movement_type="production_issue",
                reference=order.number,
                source_module="manufacturing",
                source_entity="work_order_material",
                source_id=str(line.id),
            ), from_work_order=True)
            line.issue_move_id = move.id
            db.flush()
            inventory_stock_move_service.post(
                db,
                tenant_id=tenant_id,
                company_id=company_id,
                move_id=move.id,
                user_id=user_id,
            )
            line.issued_quantity = issue_quantity
            total_component_value += (
                issue_quantity * Decimal(move.unit_cost)
            ).quantize(FOUR_PLACES, rounding=ROUND_HALF_UP)

        if total_component_value <= 0:
            raise ValueError("Production components must have a positive inventory valuation")
        output_unit_cost = (total_component_value / produced_quantity).quantize(
            FOUR_PLACES, rounding=ROUND_HALF_UP
        )
        output_value = (output_unit_cost * produced_quantity).quantize(
            FOUR_PLACES, rounding=ROUND_HALF_UP
        )
        if output_value != total_component_value:
            raise ValueError(
                "Finished-goods cost cannot exactly represent the consumed component value at the inventory cost precision"
            )

        output_move = inventory_stock_move_service.create_draft(db, StockMoveCreate(
            company_id=company_id,
            item_id=order.output_item_id,
            variant_id=order.output_variant_id,
            destination_location_id=order.destination_location_id,
            quantity=produced_quantity,
            unit_cost=output_unit_cost,
            movement_type="production_receipt",
            reference=order.number,
            source_module="manufacturing",
            source_entity="work_order_output",
            source_id=str(order.id),
        ), from_work_order=True)
        inventory_stock_move_service.post(
            db,
            tenant_id=tenant_id,
            company_id=company_id,
            move_id=output_move.id,
            user_id=user_id,
        )
        order.produced_quantity = produced_quantity
        order.status = "completed"
        order.completed_by_user_id = user_id
        order.completed_at = datetime.now(timezone.utc)
        db.flush()
        return order

    def cancel(self, db: Session, *, tenant_id: int, company_id: int, work_order_id: int, user_id: int):
        order = self.get(db, company_id=company_id, work_order_id=work_order_id, lock=True)
        if order is None:
            raise ValueError("Work order not found")
        if order.status == "cancelled":
            return order
        if order.status not in {"planned", "released", "completed"}:
            raise ValueError("Work order cannot be cancelled from its current state")
        moves = db.scalars(select(InventoryStockMove).where(
            InventoryStockMove.company_id == company_id,
            InventoryStockMove.source_module == "manufacturing",
            InventoryStockMove.reference == order.number,
            InventoryStockMove.status == "posted",
            or_(
                InventoryStockMove.source_entity == "work_order_material",
                InventoryStockMove.source_entity == "work_order_output",
            ),
        ).order_by(InventoryStockMove.id.desc()).with_for_update()).all()
        for move in moves:
            inventory_stock_move_service.reverse(
                db,
                tenant_id=tenant_id,
                company_id=company_id,
                move_id=move.id,
                user_id=user_id,
                allow_production=True,
            )
        order.status = "cancelled"
        order.produced_quantity = None
        order.completed_by_user_id = None
        order.completed_at = None
        db.flush()
        return order


manufacturing_work_order_service = ManufacturingWorkOrderService()
