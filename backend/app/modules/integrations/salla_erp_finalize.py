from __future__ import annotations

from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.commerce.accounting_service import commerce_accounting_service
from app.modules.commerce.models import SalesDocument, SalesLine
from app.modules.commerce.service import commerce_service
from app.modules.integrations.models import IntegrationMapping
from app.modules.integrations.salla_models import SallaOrder, SallaOrderItem, SallaShipment
from app.modules.inventory.items.models import InventoryItem
from app.modules.integrations.salla_erp_service import execute_salla_order, _system_user_id, reverse_salla_order
from app.modules.integrations.salla_return_service import restore_salla_inventory
from app.modules.integrations.salla_shipping_service import sync_salla_shipments_for_order


_CANCELLED_STATES = {"cancelled", "canceled", "refunded", "refund", "fully_refunded", "returned"}


def _mapping(db: Session, order: SallaOrder, entity_type: str):
    return db.scalar(select(IntegrationMapping).where(
        IntegrationMapping.company_id == order.company_id,
        IntegrationMapping.connection_id == order.connection_id,
        IntegrationMapping.entity_type == entity_type,
        IntegrationMapping.external_id == str(order.external_id),
    ))


def _set_mapping(db: Session, order: SallaOrder, entity_type: str, local_id: int):
    obj = _mapping(db, order, entity_type)
    if obj:
        obj.local_id = local_id
        return obj
    obj = IntegrationMapping(company_id=order.company_id, connection_id=order.connection_id, entity_type=entity_type, external_id=str(order.external_id), local_id=local_id)
    db.add(obj)
    db.flush()
    return obj


def _shipment_package_quantities(shipment: SallaShipment, order_items: list[SallaOrderItem]) -> dict[int, Decimal]:
    """Resolve Salla shipment packages to normalized order-item quantities."""
    packages = shipment.packages if isinstance(shipment.packages, list) else []
    if not packages:
        return {}
    by_external = {str(item.external_id): item for item in order_items}
    by_sku = {str(item.sku).strip(): item for item in order_items if item.sku}
    result: dict[int, Decimal] = {}
    for package in packages:
        if not isinstance(package, dict):
            continue
        item = None
        for key in (package.get("item_id"), package.get("external_id"), package.get("order_item_id"), package.get("id")):
            if key is not None and str(key) in by_external:
                item = by_external[str(key)]
                break
        if item is None and package.get("sku"):
            item = by_sku.get(str(package["sku"]).strip())
        try:
            quantity = Decimal(str(package.get("quantity") or 0))
        except Exception:
            quantity = Decimal("0")
        if item is not None and quantity > 0:
            result[item.id] = result.get(item.id, Decimal("0")) + quantity
    return result


def _build_delivery(db: Session, order: SallaOrder, invoice: SalesDocument, shipment: SallaShipment | None = None) -> SalesDocument | None:
    mapping_type = "salla_shipment_delivery" if shipment is not None else "salla_delivery"
    mapping_external_id = str(shipment.external_id) if shipment is not None else str(order.external_id)
    existing_map = db.scalar(select(IntegrationMapping).where(
        IntegrationMapping.company_id == order.company_id,
        IntegrationMapping.connection_id == order.connection_id,
        IntegrationMapping.entity_type == mapping_type,
        IntegrationMapping.external_id == mapping_external_id,
    ))
    if existing_map:
        return db.scalar(select(SalesDocument).where(SalesDocument.id == existing_map.local_id, SalesDocument.company_id == order.company_id))

    order_items = list(db.scalars(select(SallaOrderItem).where(
        SallaOrderItem.order_id == order.id,
        SallaOrderItem.company_id == order.company_id,
        SallaOrderItem.connection_id == order.connection_id,
    ).order_by(SallaOrderItem.id)).all())
    shipment_quantities = _shipment_package_quantities(shipment, order_items) if shipment else {}
    if shipment is not None and not shipment_quantities:
        return None

    already_delivered: dict[int, Decimal] = {}
    if shipment is not None:
        prior_maps = db.scalars(select(IntegrationMapping).where(
            IntegrationMapping.company_id == order.company_id,
            IntegrationMapping.connection_id == order.connection_id,
            IntegrationMapping.entity_type == "salla_shipment_delivery",
        )).all()
        prior_ids = [m.local_id for m in prior_maps if m.local_id]
        if prior_ids:
            prior_docs = db.scalars(select(SalesDocument).where(
                SalesDocument.company_id == order.company_id,
                SalesDocument.id.in_(prior_ids),
                SalesDocument.document_type == "delivery",
            )).all()
            for doc in prior_docs:
                for line in doc.lines:
                    already_delivered[line.item_id] = already_delivered.get(line.item_id, Decimal("0")) + Decimal(line.quantity or 0)

    stock_lines: list[SalesLine] = []
    for source_line in invoice.lines:
        item = db.scalar(select(InventoryItem).where(
            InventoryItem.id == source_line.item_id,
            InventoryItem.company_id == order.company_id,
            InventoryItem.is_active.is_(True),
        ))
        if item is None or str(item.item_type).lower() != "stockable":
            continue

        if shipment is None:
            quantity = Decimal(source_line.quantity or 0)
        else:
            matching_items = [
                oi for oi in order_items
                if oi.id in shipment_quantities
                and ((source_line.description or "") == (oi.name or "")
                     or str(item.sku or "").strip() == str(oi.sku or "").strip())
            ]
            if not matching_items:
                continue
            requested = shipment_quantities[matching_items[0].id]
            remaining = max(
                Decimal(matching_items[0].quantity or 0) - already_delivered.get(item.id, Decimal("0")),
                Decimal("0"),
            )
            quantity = min(requested, remaining)

        if quantity <= 0:
            continue
        discount_percent = Decimal(source_line.discount_percent or 0)
        line_total = (Decimal(source_line.unit_price) * quantity) * (Decimal("1") - discount_percent / Decimal("100"))
        stock_lines.append(SalesLine(
            item_id=item.id,
            variant_id=source_line.variant_id,
            tax_rate_id=None,
            tax_rate_ids=[],
            description=source_line.description,
            quantity=quantity,
            unit_price=Decimal(source_line.unit_price),
            discount_percent=discount_percent,
            tax_percent=Decimal("0"),
            line_total=line_total,
        ))

    if not stock_lines:
        return None
    if invoice.warehouse_id is None:
        raise ValueError(f"Salla order {order.external_id} cannot be fulfilled: no warehouse is configured")

    number = f"SALLA-DEL-{shipment.external_id if shipment else (order.reference_id or order.external_id)}"[:60]
    existing = db.scalar(select(SalesDocument).where(
        SalesDocument.company_id == order.company_id,
        SalesDocument.number == number,
    ))
    if existing:
        db.add(IntegrationMapping(
            company_id=order.company_id,
            connection_id=order.connection_id,
            entity_type=mapping_type,
            external_id=mapping_external_id,
            local_id=existing.id,
        ))
        db.flush()
        return existing

    delivery = SalesDocument(
        company_id=order.company_id,
        partner_id=invoice.partner_id,
        document_type="delivery",
        number=number,
        document_date=invoice.document_date,
        warehouse_id=invoice.warehouse_id,
        notes=f"Salla fulfillment for order {order.external_id}" + (f" shipment {shipment.external_id}" if shipment else ""),
        subtotal=Decimal("0"),
        tax_total=Decimal("0"),
        discount_total=Decimal("0"),
        total=Decimal("0"),
    )
    for line in stock_lines:
        delivery.lines.append(line)
        gross = Decimal(line.quantity) * Decimal(line.unit_price)
        discount = gross * Decimal(line.discount_percent or 0) / Decimal("100")
        delivery.subtotal += gross - discount
        delivery.discount_total += discount
    delivery.total = delivery.subtotal
    db.add(delivery)
    db.flush()
    db.add(IntegrationMapping(
        company_id=order.company_id,
        connection_id=order.connection_id,
        entity_type=mapping_type,
        external_id=mapping_external_id,
        local_id=delivery.id,
    ))
    db.flush()
    return delivery


_FULFILLMENT_STATES = {
    "processing", "shipped", "in_transit", "out_for_delivery",
    "delivered", "fulfilled", "partially_fulfilled", "completed",
}
_SHIPMENT_FULFILLMENT_STATES = {
    "picked_up", "pickedup", "shipped", "in_transit", "intransit",
    "received_at_final_hub", "out_for_delivery", "outfordelivery",
    "reattempted", "to_be_reattempted", "delivered", "partially_delivered",
}


def _should_fulfill_order(order: SallaOrder, *, force_fulfillment: bool = False) -> bool:
    """Inventory is consumed only after an explicit fulfillment signal."""
    if force_fulfillment:
        return True
    fulfillment = str(order.fulfillment_status or "").strip().lower().replace(" ", "_")
    state = str(order.status or "").strip().lower().replace(" ", "_")
    return fulfillment in _FULFILLMENT_STATES or state in _FULFILLMENT_STATES


def finalize_salla_order(
    db: Session,
    order: SallaOrder,
    user_id: int | None = None,
    *,
    force_fulfillment: bool = False,
    shipment: SallaShipment | None = None,
) -> dict:
    effective_user_id = user_id or _system_user_id(db, order.company_id)
    state = str(order.status or "").strip().lower().replace(" ", "_")
    payment_state = str(order.payment_status or "").strip().lower().replace(" ", "_")
    if state in _CANCELLED_STATES or payment_state in {"refunded", "fully_refunded"}:
        if order.erp_status in {"processed", "reversed"} and order.erp_entity_id:
            result = reverse_salla_order(db, order, user_id=effective_user_id)
            if result.get("status") == "reversed":
                result["inventory_return"] = restore_salla_inventory(db, order, effective_user_id)
            result["shipping"] = sync_salla_shipments_for_order(db, order)
            return result
        order.erp_status = "cancelled"
        order.erp_error = None
        db.flush()
        result = {"status": "cancelled_before_erp_execution"}
        result["shipping"] = sync_salla_shipments_for_order(db, order)
        return result

    result = execute_salla_order(db, order, user_id=effective_user_id)
    document_id = result.get("sales_document_id") or order.erp_entity_id
    if not document_id:
        result["shipping"] = sync_salla_shipments_for_order(db, order)
        return result
    invoice = db.scalar(select(SalesDocument).where(SalesDocument.id == document_id, SalesDocument.company_id == order.company_id))
    if invoice is None or invoice.document_type != "invoice":
        result["shipping"] = sync_salla_shipments_for_order(db, order)
        return result
    should_fulfill = force_fulfillment or _should_fulfill_order(order)
    delivery = _build_delivery(db, order, invoice, shipment=shipment) if should_fulfill else None
    if delivery is not None:
        if delivery.status == "draft":
            delivery.status = "confirmed"
            db.flush()
        if delivery.status in ("confirmed", "partially_fulfilled"):
            # Inventory posting owns the stock valuation/COGS journal. Do not
            # post the same COGS again through the commerce accounting layer.
            commerce_service.post_inventory(db, company_id=order.company_id, document_id=delivery.id, kind="sale", user_id=effective_user_id)
    result["delivery_document_id"] = delivery.id if delivery is not None else None
    result["shipping"] = sync_salla_shipments_for_order(db, order)
    return result
