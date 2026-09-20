from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.commerce.accounting_service import commerce_accounting_service
from app.modules.commerce.models import SalesDocument
from app.modules.integrations.models import IntegrationMapping
from app.modules.integrations.salla_models import SallaOrder
from app.modules.inventory.locations.models import InventoryLocation
from app.modules.inventory.stock_moves.models import InventoryStockMove
from app.modules.inventory.stock_moves.schemas import StockMoveCreate
from app.modules.inventory.stock_moves.service import inventory_stock_move_service


def _deliveries(db: Session, order: SallaOrder) -> list[SalesDocument]:
    mappings = db.scalars(
        select(IntegrationMapping).where(
            IntegrationMapping.company_id == order.company_id,
            IntegrationMapping.connection_id == order.connection_id,
            IntegrationMapping.external_id == str(order.external_id),
            IntegrationMapping.entity_type.in_(
                ["salla_delivery", "salla_shipment_delivery"]
            ),
        )
    ).all()
    ids = {m.local_id for m in mappings if m.local_id}
    if not ids:
        return []
    return db.scalars(
        select(SalesDocument).where(
            SalesDocument.id.in_(ids),
            SalesDocument.company_id == order.company_id,
            SalesDocument.document_type == "delivery",
        )
    ).all()


def restore_salla_inventory(db: Session, order: SallaOrder, user_id: int) -> dict:
    """Restore fulfilled Salla stock exactly once and reverse its COGS."""
    deliveries = _deliveries(db, order)
    if not deliveries:
        return {"status": "no_delivery", "return_moves": 0, "cogs_reversed": False}

    all_source_moves = []
    for delivery in deliveries:
        if not delivery.warehouse_id:
            continue
        all_source_moves.extend(db.scalars(
            select(InventoryStockMove).where(
                InventoryStockMove.company_id == order.company_id,
                InventoryStockMove.source_module == "commerce",
                InventoryStockMove.source_entity == "sales_delivery",
                InventoryStockMove.source_id.like(f"{delivery.id}:%"),
                InventoryStockMove.status == "posted",
            )
        ).all())

    source_moves = db.scalars(
        select(InventoryStockMove).where(
            InventoryStockMove.company_id == order.company_id,
            InventoryStockMove.source_module == "commerce",
            InventoryStockMove.source_entity == "sales_delivery",
            InventoryStockMove.source_id.like(f"{delivery.id}:%"),
            InventoryStockMove.status == "posted",
        )
    ).all()
    if not source_moves:
        return {"status": "delivery_not_posted", "return_moves": 0, "cogs_reversed": False}

    delivery_for_location = deliveries[0]
    destination = db.scalar(
        select(InventoryLocation).where(
            InventoryLocation.warehouse_id == delivery_for_location.warehouse_id,
            InventoryLocation.company_id == order.company_id,
            InventoryLocation.is_active.is_(True),
        ).order_by(InventoryLocation.id)
    )
    if destination is None:
        raise ValueError(f"Salla return {order.external_id} cannot restore stock: warehouse has no active location")

    total_cost = Decimal("0")
    returned = 0
    for move in source_moves:
        source_id = f"{order.external_id}:{move.id}"
        existing = db.scalar(
            select(InventoryStockMove).where(
                InventoryStockMove.company_id == order.company_id,
                InventoryStockMove.source_module == "integrations",
                InventoryStockMove.source_entity == "salla_return",
                InventoryStockMove.source_id == source_id,
                InventoryStockMove.status == "posted",
            )
        )
        if existing:
            total_cost += Decimal(existing.quantity) * Decimal(existing.unit_cost or 0)
            returned += 1
            continue

        payload = StockMoveCreate(
            company_id=order.company_id,
            item_id=move.item_id,
            movement_type="receipt",
            source_location_id=None,
            destination_location_id=destination.id,
            quantity=Decimal(move.quantity),
            unit_cost=Decimal(move.unit_cost or 0),
            reference=f"SALLA-RET-{order.reference_id or order.external_id}"[:80],
            notes=f"Salla return for order {order.external_id}",
        )
        ret = inventory_stock_move_service.create_draft(db, payload)
        ret.source_module = "integrations"
        ret.source_entity = "salla_return"
        ret.source_id = source_id
        inventory_stock_move_service.post(db, company_id=order.company_id, move_id=ret.id)
        total_cost += Decimal(ret.quantity) * Decimal(ret.unit_cost or 0)
        returned += 1

    accounting = False
    if total_cost > 0:
        settings = commerce_accounting_service._settings(db, order.company_id)
        commerce_accounting_service._post(
            db,
            company_id=order.company_id,
            user_id=user_id,
            entry_date=delivery_for_location.document_date,
            journal_id=settings.sales_journal_id,
            entry_number=f"RET-COGS-{order.external_id}",
            description=f"COGS reversal for Salla return {order.external_id}",
            lines=[
                {"account_combination_id": settings.inventory_account_id, "debit": total_cost, "credit": 0},
                {"account_combination_id": settings.cogs_account_id, "debit": 0, "credit": total_cost},
            ],
            source_entity="salla_return_cogs",
            source_id=hash(order.external_id),
        )
        accounting = True
    return {"status": "restored", "return_moves": returned, "cogs_reversed": accounting}
