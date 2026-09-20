from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.commerce.accounting_service import commerce_accounting_service
from app.modules.commerce.models import SalesDocument
from app.modules.integrations.models import IntegrationMapping
from app.modules.integrations.salla_models import SallaOrder, SallaShipment
from app.modules.inventory.locations.models import InventoryLocation
from app.modules.inventory.stock_moves.models import InventoryStockMove
from app.modules.inventory.stock_moves.schemas import StockMoveCreate
from app.modules.inventory.stock_moves.service import inventory_stock_move_service


def _deliveries(db: Session, order: SallaOrder, shipment_external_id: str | None = None) -> list[SalesDocument]:
    """Resolve every ERP delivery created for this Salla order.

    Order-level deliveries are keyed by the order external ID, while
    shipment-level deliveries are keyed by the shipment external ID. Looking
    up only the order ID would silently miss partial-shipment deliveries.
    """
    external_ids = {str(order.external_id)} if shipment_external_id is None else set()
    shipment_ids = db.scalars(
        select(SallaShipment.external_id).where(
            SallaShipment.company_id == order.company_id,
            SallaShipment.connection_id == order.connection_id,
            (
                (SallaShipment.order_id == order.id)
                | (SallaShipment.order_external_id == str(order.external_id))
            ),
        )
    ).all()
    external_ids.update(str(value) for value in shipment_ids if value)
    if shipment_external_id is not None:
        external_ids = {str(shipment_external_id)}

    mappings = db.scalars(
        select(IntegrationMapping).where(
            IntegrationMapping.company_id == order.company_id,
            IntegrationMapping.connection_id == order.connection_id,
            IntegrationMapping.external_id.in_(external_ids),
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
        ).order_by(SalesDocument.id)
    ).all()


def _return_source_id(order_external_id: str, move_id: int) -> str:
    """Return idempotency key for one original Salla fulfillment stock move.

    The key deliberately does not include the shipment/event scope so a later
    order-level return cannot restore a move that was already restored by a
    shipment-level return.
    """
    return f"salla_return:{order_external_id}:{move_id}"


def restore_salla_inventory(db: Session, order: SallaOrder, user_id: int, shipment_external_id: str | None = None) -> dict:
    """Restore fulfilled Salla stock exactly once and reverse its COGS."""
    deliveries = _deliveries(db, order, shipment_external_id=shipment_external_id)
    if not deliveries:
        return {"status": "no_delivery", "return_moves": 0, "cogs_reversed": False}

    source_moves = []
    for delivery in deliveries:
        if not delivery.warehouse_id:
            continue
        source_moves.extend(db.scalars(
            select(InventoryStockMove).where(
                InventoryStockMove.company_id == order.company_id,
                InventoryStockMove.source_module == "commerce",
                InventoryStockMove.source_entity == "sales_delivery",
                InventoryStockMove.source_id.like(f"{delivery.id}:%"),
                InventoryStockMove.status == "posted",
            )
        ).all())
    if not source_moves:
        return {"status": "delivery_not_posted", "return_moves": 0, "cogs_reversed": False}

    delivery_for_location = next((d for d in deliveries if d.warehouse_id), None)
    if delivery_for_location is None:
        return {"status": "delivery_without_warehouse", "return_moves": 0, "cogs_reversed": False}
    destination = db.scalar(
        select(InventoryLocation).where(
            InventoryLocation.warehouse_id == delivery_for_location.warehouse_id,
            InventoryLocation.company_id == order.company_id,
            InventoryLocation.is_active.is_(True),
        ).order_by(InventoryLocation.id)
    )
    if destination is None:
        raise ValueError(f"Salla return {order.external_id} cannot restore stock: warehouse has no active location")

    return_key = f"{order.external_id}:shipment:{shipment_external_id}" if shipment_external_id else str(order.external_id)
    total_cost = Decimal("0")
    returned = 0
    newly_returned = 0
    for move in source_moves:
        source_id = _return_source_id(str(order.external_id), move.id)
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
            # This move was already restored by an earlier shipment/order
            # return. Do not count it again for COGS or create another receipt.
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
        newly_returned += 1

    accounting = False
    if newly_returned == 0:
        return {"status": "already_restored", "return_moves": 0, "cogs_reversed": False}
    if total_cost > 0:
        settings = commerce_accounting_service._settings(db, order.company_id)
        commerce_accounting_service._post(
            db,
            company_id=order.company_id,
            user_id=user_id,
            entry_date=delivery_for_location.document_date,
            journal_id=settings.sales_journal_id,
            entry_number=f"RET-COGS-{return_key}"[:60],
            description=f"COGS reversal for Salla return {order.external_id}",
            lines=[
                {"account_combination_id": settings.inventory_account_id, "debit": total_cost, "credit": 0},
                {"account_combination_id": settings.cogs_account_id, "debit": 0, "credit": total_cost},
            ],
            source_entity="salla_return_cogs",
            source_id=return_key,
        )
        accounting = True
    return {"status": "restored", "return_moves": returned, "cogs_reversed": accounting}
