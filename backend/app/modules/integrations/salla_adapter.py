import json
from datetime import date
from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.accounting.models import TaxRate
from app.modules.commerce.models import BusinessPartner, SalesDocument, SalesLine
from app.modules.inventory.items.models import InventoryItem

from .models import IntegrationConnection, IntegrationEvent
from .salla_models import SallaExternalMapping
from .salla_settings import SallaSyncSettings


def _decimal(value, default="0") -> Decimal:
    if value is None:
        return Decimal(default)
    if isinstance(value, dict):
        value = value.get("amount", value.get("value", default))
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"Invalid numeric value: {value!r}")


def _text(value, fallback="") -> str:
    if value is None:
        return fallback
    if isinstance(value, dict):
        value = value.get("name", value.get("value", fallback))
    return str(value).strip()


def _data(payload: dict) -> dict:
    value = payload.get("data", payload)
    return value if isinstance(value, dict) else {}


def _external_id(value, *keys) -> str | None:
    if isinstance(value, dict):
        for key in keys:
            candidate = value.get(key)
            if candidate is not None and str(candidate).strip():
                return str(candidate)
    elif value is not None:
        return str(value)
    return None


def _mapping(db: Session, connection_id: int, entity_type: str, external_id: str):
    return db.scalar(
        select(SallaExternalMapping)
        .where(
            SallaExternalMapping.connection_id == connection_id,
            SallaExternalMapping.entity_type == entity_type,
            SallaExternalMapping.external_id == external_id,
        )
        .with_for_update()
    )


def _settings(db: Session, connection_id: int) -> SallaSyncSettings:
    settings = db.scalar(
        select(SallaSyncSettings).where(
            SallaSyncSettings.connection_id == connection_id,
            SallaSyncSettings.active.is_(True),
        )
    )
    if settings is None:
        raise ValueError("Salla sync settings are not configured for this connection")
    return settings


def _save_mapping(db, connection, entity_type, external_id, internal_id, payload):
    mapping = _mapping(db, connection.id, entity_type, external_id)
    serialized = json.dumps(payload, ensure_ascii=False) if isinstance(payload, dict) else None
    if mapping is None:
        mapping = SallaExternalMapping(
            company_id=connection.company_id,
            connection_id=connection.id,
            entity_type=entity_type,
            external_id=external_id,
            internal_id=internal_id,
            payload=serialized,
            is_active=True,
        )
        db.add(mapping)
    else:
        mapping.internal_id = internal_id
        mapping.payload = serialized
        mapping.is_active = True
    db.flush()
    return mapping


def _customer(db, connection, settings, data: dict) -> BusinessPartner:
    customer = data.get("customer") or data.get("buyer") or {}
    external_id = _external_id(customer, "id", "customer_id") or _external_id(data, "customer_id", "user_id")
    if not external_id:
        raise ValueError("Salla order has no customer id")
    mapping = _mapping(db, connection.id, "customer", external_id)
    if mapping and mapping.internal_id:
        obj = db.scalar(select(BusinessPartner).where(BusinessPartner.id == mapping.internal_id, BusinessPartner.company_id == connection.company_id))
        if obj:
            return obj

    code = f"{settings.customer_code_prefix}{external_id}"[:50]
    obj = db.scalar(select(BusinessPartner).where(BusinessPartner.company_id == connection.company_id, BusinessPartner.code == code))
    name = _text(customer.get("name")) or "Salla Customer"
    phone = _text(customer.get("mobile")) or _text(customer.get("phone")) or None
    email = _text(customer.get("email")) or None
    if obj is None:
        obj = BusinessPartner(company_id=connection.company_id, code=code, name=name, partner_type="customer", phone=phone, email=email, is_active=True)
        db.add(obj)
        db.flush()
    else:
        obj.name = name or obj.name
        obj.phone = phone or obj.phone
        obj.email = email or obj.email
    _save_mapping(db, connection, "customer", external_id, obj.id, customer)
    return obj


def _product(db, connection, settings, line: dict) -> InventoryItem:
    product = line.get("product") if isinstance(line.get("product"), dict) else line
    external_id = _external_id(product, "id", "product_id")
    if not external_id:
        raise ValueError("Salla order line has no product id")
    mapping = _mapping(db, connection.id, "product", external_id)
    if mapping and mapping.internal_id:
        obj = db.scalar(select(InventoryItem).where(InventoryItem.id == mapping.internal_id, InventoryItem.company_id == connection.company_id))
        if obj:
            return obj

    sku = _text(product.get("sku")) or f"{settings.product_code_prefix}{external_id}"
    sku = sku[:80]
    obj = db.scalar(select(InventoryItem).where(InventoryItem.company_id == connection.company_id, InventoryItem.sku == sku))
    name = _text(product.get("name")) or _text(product.get("title")) or f"Salla Product {external_id}"
    barcode = _text(product.get("barcode")) or None
    price = _decimal(line.get("price", product.get("price", "0")))
    if obj is None:
        obj = InventoryItem(company_id=connection.company_id, sku=sku, barcode=barcode, name_ar=name[:200], name_en=name[:200], item_type="stockable", uom="unit", costing_method="weighted_average", sales_price=price, purchase_price=Decimal("0"), standard_cost=Decimal("0"), reorder_level=Decimal("0"), is_active=True)
        db.add(obj)
        db.flush()
    else:
        obj.name_ar = name[:200]
        obj.name_en = name[:200]
        if barcode:
            obj.barcode = barcode
        if price >= 0:
            obj.sales_price = price
    _save_mapping(db, connection, "product", external_id, obj.id, product)
    return obj


def import_salla_order(db: Session, event: IntegrationEvent) -> SalesDocument:
    connection = db.get(IntegrationConnection, event.connection_id)
    if connection is None or connection.provider.lower() != "salla":
        raise ValueError("Salla connection not found")
    settings = _settings(db, connection.id)
    payload = json.loads(event.payload or "{}")
    data = _data(payload)
    external_order_id = _external_id(data, "id", "order_id") or _external_id(payload, "order_id")
    if not external_order_id:
        raise ValueError("Salla order event has no order id")

    mapping = _mapping(db, connection.id, "order", external_order_id)
    if mapping and mapping.internal_id:
        existing = db.scalar(select(SalesDocument).where(SalesDocument.id == mapping.internal_id, SalesDocument.company_id == connection.company_id).with_for_update())
        if existing:
            return existing

    partner = _customer(db, connection, settings, data)
    raw_lines = data.get("items") or data.get("products") or data.get("order_items") or []
    if not isinstance(raw_lines, list) or not raw_lines:
        raise ValueError("Salla order contains no items")

    tax_amount = _decimal(data.get("tax_amount", data.get("tax", "0")))
    default_tax = None
    if settings.default_tax_rate_id:
        default_tax = db.scalar(select(TaxRate).where(TaxRate.id == settings.default_tax_rate_id, TaxRate.company_id == connection.company_id, TaxRate.is_active.is_(True), TaxRate.is_withholding.is_(False)))
        if default_tax is None:
            raise ValueError("Configured Salla default tax rate is invalid")
    if tax_amount != 0 and default_tax is None:
        raise ValueError("Salla order has tax but no default VAT Tax Master is configured")

    number = f"SALLA-{external_order_id}"[:60]
    existing = db.scalar(select(SalesDocument).where(SalesDocument.company_id == connection.company_id, SalesDocument.number == number).with_for_update())
    if existing:
        _save_mapping(db, connection, "order", external_order_id, existing.id, data)
        return existing

    document = SalesDocument(
        company_id=connection.company_id,
        partner_id=partner.id,
        document_type="order",
        number=number,
        document_date=date.today(),
        warehouse_id=settings.warehouse_id,
        notes=f"Imported from Salla order {external_order_id}",
        status="confirmed",
    )
    subtotal = Decimal("0")
    tax_total = Decimal("0")
    for raw_line in raw_lines:
        if not isinstance(raw_line, dict):
            continue
        item = _product(db, connection, settings, raw_line)
        quantity = _decimal(raw_line.get("quantity", raw_line.get("qty", "1")))
        if quantity <= 0:
            raise ValueError("Salla order line quantity must be positive")
        unit_price = _decimal(raw_line.get("price", raw_line.get("unit_price", item.sales_price)))
        if unit_price < 0:
            raise ValueError("Salla order line price cannot be negative")
        discount = _decimal(raw_line.get("discount_percent", "0"))
        if discount < 0 or discount > 100:
            raise ValueError("Salla order line discount is outside 0-100%")
        net = quantity * unit_price * (Decimal("1") - discount / Decimal("100"))
        tax_percent = Decimal(default_tax.rate) if default_tax else Decimal("0")
        line_tax = net * tax_percent / Decimal("100")
        document.lines.append(SalesLine(item_id=item.id, tax_rate_id=default_tax.id if default_tax else None, description=_text(raw_line.get("name"))[:250] or item.name_ar, quantity=quantity, unit_price=unit_price, discount_percent=discount, tax_percent=tax_percent, line_total=net + line_tax))
        subtotal += net
        tax_total += line_tax

    if not document.lines:
        raise ValueError("Salla order contains no valid item lines")
    document.subtotal = subtotal
    document.tax_total = tax_total
    document.discount_total = sum((Decimal(str(line.quantity)) * Decimal(str(line.unit_price)) * Decimal(str(line.discount_percent)) / Decimal("100") for line in document.lines), Decimal("0"))
    document.total = subtotal + tax_total
    db.add(document)
    db.flush()
    _save_mapping(db, connection, "order", external_order_id, document.id, data)
    return document
