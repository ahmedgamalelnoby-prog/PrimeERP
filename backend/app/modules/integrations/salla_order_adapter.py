from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.accounting.models import TaxRate
from app.modules.commerce.models import BusinessPartner, SalesDocument, SalesLine
from app.modules.inventory.items.models import InventoryItem
from app.modules.inventory.warehouses.models import InventoryWarehouse

from .models import IntegrationConnection, IntegrationEvent
from .salla_models import SallaExternalMapping
from .salla_settings import SallaSyncSettings


def _decimal(value, default=Decimal("0")) -> Decimal:
    if value is None or value == "":
        return default
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"Invalid numeric Salla value: {value}") from exc


def _text(value, fallback="") -> str:
    if isinstance(value, dict):
        value = value.get("name") or value.get("ar") or value.get("en")
    return str(value or fallback).strip()


def _id(value):
    if isinstance(value, dict):
        return value.get("id")
    return value


def _mapping(db, connection_id: int, entity_type: str, external_id: str):
    return db.scalar(select(SallaExternalMapping).where(
        SallaExternalMapping.connection_id == connection_id,
        SallaExternalMapping.entity_type == entity_type,
        SallaExternalMapping.external_id == str(external_id),
        SallaExternalMapping.is_active.is_(True),
    ).with_for_update())


def _upsert_mapping(db, connection, entity_type, external_id, internal_id, payload):
    mapping = _mapping(db, connection.id, entity_type, str(external_id))
    if mapping is None:
        mapping = SallaExternalMapping(
            company_id=connection.company_id,
            connection_id=connection.id,
            entity_type=entity_type,
            external_id=str(external_id),
            internal_id=internal_id,
            payload=payload,
            is_active=True,
        )
        db.add(mapping)
    else:
        mapping.internal_id = internal_id
        mapping.payload = payload
        mapping.is_active = True
    db.flush()
    return mapping


def _customer(db: Session, connection, settings, data: dict) -> BusinessPartner:
    external_id = _id(data.get("id") or data.get("customer_id"))
    if not external_id:
        raise ValueError("Salla order customer id is required")
    mapping = _mapping(db, connection.id, "customer", str(external_id))
    if mapping and mapping.internal_id:
        customer = db.scalar(select(BusinessPartner).where(
            BusinessPartner.id == mapping.internal_id,
            BusinessPartner.company_id == connection.company_id,
        ).with_for_update())
        if customer:
            return customer

    code = f"{settings.customer_code_prefix}{external_id}"[:50]
    customer = db.scalar(select(BusinessPartner).where(
        BusinessPartner.company_id == connection.company_id,
        BusinessPartner.code == code,
    ).with_for_update())
    if customer is None:
        customer = BusinessPartner(
            company_id=connection.company_id,
            code=code,
            name=_text(data.get("name"), f"Salla Customer {external_id}"),
            partner_type="customer",
            tax_number=_text(data.get("tax_number")) or None,
            phone=_text(data.get("mobile") or data.get("phone")) or None,
            email=_text(data.get("email")) or None,
            is_active=True,
        )
        db.add(customer)
        db.flush()
    else:
        customer.name = _text(data.get("name"), customer.name)
        customer.phone = _text(data.get("mobile") or data.get("phone"), customer.phone or "") or customer.phone
        customer.email = _text(data.get("email"), customer.email or "") or customer.email
    _upsert_mapping(db, connection, "customer", str(external_id), customer.id, None)
    return customer


def _product(db: Session, connection, settings, data: dict) -> InventoryItem:
    external_id = _id(data.get("id") or data.get("product_id"))
    if not external_id:
        raise ValueError("Salla order line product id is required")
    mapping = _mapping(db, connection.id, "product", str(external_id))
    if mapping and mapping.internal_id:
        item = db.scalar(select(InventoryItem).where(
            InventoryItem.id == mapping.internal_id,
            InventoryItem.company_id == connection.company_id,
        ).with_for_update())
        if item:
            return item

    sku = _text(data.get("sku") or data.get("reference_id")) or f"{settings.product_code_prefix}{external_id}"[:80]
    item = db.scalar(select(InventoryItem).where(
        InventoryItem.company_id == connection.company_id,
        InventoryItem.sku == sku,
    ).with_for_update())
    if item is None:
        item = InventoryItem(
            company_id=connection.company_id,
            sku=sku,
            barcode=_text(data.get("barcode")) or None,
            name_ar=_text(data.get("name"), f"Salla Product {external_id}"),
            name_en=_text(data.get("name_en")) or None,
            item_type="stockable",
            uom="unit",
            costing_method="weighted_average",
            sales_price=_decimal(data.get("price") or data.get("regular_price")),
            purchase_price=Decimal("0"),
            standard_cost=Decimal("0"),
            reorder_level=Decimal("0"),
            is_active=True,
        )
        db.add(item)
        db.flush()
    else:
        item.name_ar = _text(data.get("name"), item.name_ar)
        if data.get("barcode"):
            item.barcode = _text(data.get("barcode"))
        if data.get("price") is not None:
            item.sales_price = _decimal(data.get("price"))
    _upsert_mapping(db, connection, "product", str(external_id), item.id, None)
    return item


def import_salla_order(db: Session, event: IntegrationEvent) -> SalesDocument:
    connection = db.get(IntegrationConnection, event.connection_id)
    if connection is None or connection.provider.lower() != "salla" or not connection.is_active:
        raise ValueError("Active Salla connection not found")
    settings = db.scalar(select(SallaSyncSettings).where(
        SallaSyncSettings.connection_id == connection.id,
        SallaSyncSettings.active.is_(True),
    ))
    if settings is None:
        raise ValueError("Salla sync settings are required before importing orders")

    payload = event.payload
    if isinstance(payload, str):
        import json
        payload = json.loads(payload)
    if not isinstance(payload, dict):
        raise ValueError("Salla order payload must be an object")
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    external_order_id = _id(data.get("id") or data.get("order_id"))
    if not external_order_id:
        raise ValueError("Salla order id is required")

    mapping = _mapping(db, connection.id, "order", str(external_order_id))
    if mapping and mapping.internal_id:
        order = db.scalar(select(SalesDocument).where(
            SalesDocument.id == mapping.internal_id,
            SalesDocument.company_id == connection.company_id,
        ).with_for_update())
        if order:
            return order

    customer_data = data.get("customer") if isinstance(data.get("customer"), dict) else data.get("customer_details", {})
    customer = _customer(db, connection, settings, customer_data or {})

    lines = data.get("items") or data.get("line_items") or []
    if not isinstance(lines, list) or not lines:
        raise ValueError("Salla order contains no line items")

    tax_rate = None
    tax_amount = _decimal(data.get("tax_amount") or data.get("tax"))
    if tax_amount > 0:
        if not settings.default_tax_rate_id:
            raise ValueError("Salla order has tax but no default Tax Master is configured")
        tax_rate = db.scalar(select(TaxRate).where(
            TaxRate.id == settings.default_tax_rate_id,
            TaxRate.company_id == connection.company_id,
            TaxRate.is_active.is_(True),
            TaxRate.is_withholding.is_(False),
        ))
        if tax_rate is None:
            raise ValueError("Configured Salla default tax rate is invalid")

    warehouse_id = settings.warehouse_id
    if warehouse_id:
        warehouse = db.scalar(select(InventoryWarehouse).where(
            InventoryWarehouse.id == warehouse_id,
            InventoryWarehouse.company_id == connection.company_id,
            InventoryWarehouse.is_active.is_(True),
        ))
        if warehouse is None:
            raise ValueError("Configured Salla warehouse is invalid")

    number = f"SALLA-{external_order_id}"[:60]
    existing = db.scalar(select(SalesDocument).where(
        SalesDocument.company_id == connection.company_id,
        SalesDocument.number == number,
    ).with_for_update())
    if existing:
        _upsert_mapping(db, connection, "order", str(external_order_id), existing.id, None)
        return existing

    order = SalesDocument(
        company_id=connection.company_id,
        partner_id=customer.id,
        document_type="order",
        number=number,
        document_date=date.today(),
        status="draft",
        warehouse_id=warehouse_id,
        notes=f"Imported from Salla order {external_order_id}",
    )
    subtotal = Decimal("0")
    discount = Decimal("0")
    computed_tax = Decimal("0")
    for raw in lines:
        product_data = raw.get("product") if isinstance(raw.get("product"), dict) else raw
        item = _product(db, connection, settings, product_data)
        quantity = _decimal(raw.get("quantity"), Decimal("1"))
        if quantity <= 0:
            raise ValueError("Salla order line quantity must be positive")
        price = _decimal(raw.get("price") or raw.get("unit_price") or product_data.get("price"))
        line_discount = _decimal(raw.get("discount") or raw.get("discount_amount"))
        gross = quantity * price
        net = gross - line_discount
        if net < 0:
            raise ValueError("Salla order line discount exceeds gross value")
        line_tax = Decimal("0")
        if tax_rate:
            line_tax = net * Decimal(tax_rate.rate) / Decimal("100")
        order.lines.append(SalesLine(
            item_id=item.id,
            tax_rate_id=tax_rate.id if tax_rate else None,
            description=_text(product_data.get("name"), item.name_ar)[:250],
            quantity=quantity,
            unit_price=price,
            discount_percent=(line_discount / gross * Decimal("100")) if gross else Decimal("0"),
            tax_percent=Decimal(tax_rate.rate) if tax_rate else Decimal("0"),
            line_total=net + line_tax,
        ))
        subtotal += net
        discount += line_discount
        computed_tax += line_tax

    if tax_amount > 0:
        tolerance = Decimal("0.01")
        if abs(computed_tax - tax_amount) > tolerance:
            raise ValueError("Salla tax amount does not reconcile with configured Tax Master")
    order.subtotal = subtotal
    order.discount_total = discount
    order.tax_total = computed_tax
    order.total = subtotal + computed_tax
    db.add(order)
    db.flush()
    _upsert_mapping(db, connection, "order", str(external_order_id), order.id, None)
    return order
