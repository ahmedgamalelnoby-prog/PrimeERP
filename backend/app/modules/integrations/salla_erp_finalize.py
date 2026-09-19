from __future__ import annotations

from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.commerce.accounting_service import commerce_accounting_service
from app.modules.commerce.models import SalesDocument, SalesLine
from app.modules.commerce.service import commerce_service
from app.modules.integrations.models import IntegrationMapping
from app.modules.integrations.salla_models import SallaOrder
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


def _build_delivery(db: Session, order: SallaOrder, invoice: SalesDocument) -> SalesDocument | None:
    existing_map = _mapping(db, order, "salla_delivery")
    if existing_map:
        return db.scalar(select(SalesDocument).where(SalesDocument.id == existing_map.local_id, SalesDocument.company_id == order.company_id))
    stock_lines: list[SalesLine] = []
    for source_line in invoice.lines:
        item = db.scalar(select(InventoryItem).where(InventoryItem.id == source_line.item_id, InventoryItem.company_id == order.company_id, InventoryItem.is_active.is_(True)))
        if item is None or str(item.item_type).lower() != "stockable":
            continue
        stock_lines.append(SalesLine(item_id=item.id, tax_rate_id=None, tax_rate_ids=[], description=source_line.description, quantity=Decimal(source_line.quantity), unit_price=Decimal(source_line.unit_price), discount_percent=Decimal(source_line.discount_percent or 0), tax_percent=Decimal("0"), line_total=Decimal(source_line.line_total or 0)))
    if not stock_lines:
        return None
    if invoice.warehouse_id is None:
        raise ValueError(f"Salla order {order.external_id} cannot be fulfilled: no warehouse is configured")
    number = f"SALLA-DEL-{order.reference_id or order.external_id}"[:60]
    existing = db.scalar(select(SalesDocument).where(SalesDocument.company_id == order.company_id, SalesDocument.number == number))
    if existing:
        _set_mapping(db, order, "salla_delivery", existing.id)
        return existing
    delivery = SalesDocument(company_id=order.company_id, partner_id=invoice.partner_id, document_type="delivery", number=number, document_date=invoice.document_date, warehouse_id=invoice.warehouse_id, notes=f"Salla fulfillment for order {order.external_id}", subtotal=Decimal("0"), tax_total=Decimal("0"), discount_total=Decimal("0"), total=Decimal("0"))
    for line in stock_lines:
        delivery.lines.append(line)
        gross = Decimal(line.quantity) * Decimal(line.unit_price)
        discount = gross * Decimal(line.discount_percent or 0) / Decimal("100")
        delivery.subtotal += gross - discount
        delivery.discount_total += discount
    delivery.total = delivery.subtotal
    db.add(delivery)
    db.flush()
    _set_mapping(db, order, "salla_delivery", delivery.id)
    return delivery


def finalize_salla_order(db: Session, order: SallaOrder, user_id: int | None = None) -> dict:
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
    delivery = _build_delivery(db, order, invoice)
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
