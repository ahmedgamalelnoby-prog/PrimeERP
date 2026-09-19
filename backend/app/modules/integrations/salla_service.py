from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import IntegrationConnection, IntegrationEvent
from .salla_models import SallaCustomer, SallaInvoice, SallaOrder, SallaOrderItem, SallaProduct, SallaProductVariant, SallaShipment
from .salla_product_mapping_service import reconcile_salla_product_mapping


def _dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _id(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, dict):
        value = value.get("id") or value.get("value")
    return str(value) if value is not None else None


def _code(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, dict):
        value = value.get("slug") or value.get("code") or value.get("key") or value.get("name") or value.get("value") or value.get("id")
    return str(value) if value is not None else None


def _decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    if isinstance(value, dict):
        value = value.get("amount") if value.get("amount") is not None else value.get("value")
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _dt(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def _date(value: Any) -> date | None:
    if not value:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def _data(payload: dict) -> dict:
    data = payload.get("data")
    return data if isinstance(data, dict) else payload


def _event_key(event_type: str) -> str:
    value = event_type.lower().replace("_", ".")
    if "invoice" in value:
        return "invoice"
    if value.startswith("order"):
        return "order"
    if value.startswith("product"):
        return "product"
    if value.startswith("customer"):
        return "customer"
    if value.startswith("shipment") or ".shipment." in value:
        return "shipment"
    return "unknown"


def _upsert(db: Session, model, connection_id: int, external_id: str, values: dict):
    # A connection belongs to exactly one company. Keep the company scope in
    # every read/update so a reused/misconfigured connection ID can never
    # mutate another company's synchronized Salla records.
    company_id = values.get("company_id")
    if company_id is None:
        raise ValueError("Salla synchronization requires a company scope")
    connection = db.scalar(
        select(IntegrationConnection).where(
            IntegrationConnection.id == connection_id,
            IntegrationConnection.company_id == company_id,
            IntegrationConnection.is_active.is_(True),
        )
    )
    if connection is None:
        raise ValueError("Salla connection does not belong to the company or is inactive")
    obj = db.scalar(
        select(model).where(
            model.connection_id == connection_id,
            model.company_id == company_id,
            model.external_id == external_id,
        ).with_for_update()
    )
    if obj is None:
        obj = model(connection_id=connection_id, external_id=external_id, **values)
        db.add(obj)
    else:
        for key, value in values.items():
            setattr(obj, key, value)
    return obj


def _normalize_customer(db: Session, company_id: int, connection_id: int, data: dict) -> SallaCustomer | None:
    external_id = _id(data.get("id") or data.get("customer_id"))
    if not external_id:
        return None
    return _upsert(db, SallaCustomer, connection_id, external_id, {
        "company_id": company_id, "first_name": data.get("first_name"), "last_name": data.get("last_name"),
        "mobile": data.get("mobile"), "mobile_code": data.get("mobile_code"), "email": data.get("email"),
        "gender": data.get("gender"), "city": data.get("city"), "country": data.get("country"),
        "country_code": data.get("country_code"), "location": _dict(data.get("location")), "urls": _dict(data.get("urls")),
        "groups": _list(data.get("groups")), "updated_at_salla": _dt(data.get("updated_at")), "raw_payload": data,
    })


def _normalize_product(db: Session, company_id: int, connection_id: int, data: dict) -> SallaProduct | None:
    external_id = _id(data.get("id") or data.get("product_id"))
    if not external_id:
        return None
    obj = _upsert(db, SallaProduct, connection_id, external_id, {
        "company_id": company_id, "sku": data.get("sku"), "mpn": data.get("mpn"), "gtin": data.get("gtin"),
        "product_type": data.get("type"), "name": data.get("name"), "status": _code(data.get("status")),
        "price": _decimal(data.get("price")), "taxed_price": _decimal(data.get("taxed_price")), "pre_tax_price": _decimal(data.get("pre_tax_price")),
        "tax": _decimal(data.get("tax")), "sale_price": _decimal(data.get("sale_price")), "cost_price": _decimal(data.get("cost_price")),
        "quantity": _decimal(data.get("quantity")), "weight": _decimal(data.get("weight")), "weight_type": data.get("weight_type"),
        "weight_unit": data.get("weight_unit"), "currency": data.get("currency"), "require_shipping": data.get("require_shipping"),
        "is_available": data.get("is_available"), "unlimited_quantity": data.get("unlimited_quantity"), "sold_quantity": _decimal(data.get("sold_quantity")),
        "regular_price": _decimal(data.get("regular_price")), "maximum_quantity_per_order": _decimal(data.get("maximum_quantity_per_order")),
        "max_items_per_user": _decimal(data.get("max_items_per_user")), "notify_quantity": _decimal(data.get("notify_quantity")),
        "category_ids": _list(data.get("categories") or data.get("category_ids")), "brand": _dict(data.get("brand")),
        "channels": _list(data.get("channels")), "options": _list(data.get("options")), "metadata_json": _dict(data.get("metadata")),
        "urls": _dict(data.get("urls")), "images": _list(data.get("images")), "updated_at_salla": _dt(data.get("updated_at")), "raw_payload": data,
    })
    db.flush()
    before = db.query(SallaProductVariant).filter(SallaProductVariant.company_id == company_id, SallaProductVariant.connection_id == connection_id, SallaProductVariant.product_id == obj.id).count()
    for variant in _list(data.get("skus") or data.get("variants")):
        variant = _dict(variant)
        variant_id = _id(variant.get("id") or variant.get("sku_id"))
        if not variant_id:
            continue
        _upsert(db, SallaProductVariant, connection_id, variant_id, {
            "company_id": company_id, "product_id": obj.id, "sku": variant.get("sku"), "barcode": variant.get("barcode"),
            "mpn": variant.get("mpn"), "gtin": variant.get("gtin"), "price": _decimal(variant.get("price")),
            "regular_price": _decimal(variant.get("regular_price")), "cost_price": _decimal(variant.get("cost_price")),
            "sale_price": _decimal(variant.get("sale_price")), "stock": _decimal(variant.get("stock") or variant.get("quantity")),
            "weight": _decimal(variant.get("weight")), "weight_type": variant.get("weight_type"),
            "option_values": _list(variant.get("related_options") or variant.get("options")), "raw_payload": variant,
        })
    db.flush()
    try:
        reconcile_result = reconcile_salla_product_mapping(db, company_id=company_id, connection_id=connection_id, salla_product_id=obj.id)
    except ValueError as exc:
        # A SKU-bearing commerce product is not a successfully synchronized
        # product until its ERP recipe identity is resolved. Let the event
        # processor retry the transaction instead of silently recording a
        # partial product with a mapping error.
        variant_rows = _list(data.get("skus") or data.get("variants"))
        sku_bearing = bool(data.get("sku")) or any(
            isinstance(row, dict) and (row.get("sku") or row.get("barcode") or row.get("gtin"))
            for row in variant_rows
        )
        if sku_bearing:
            raise
        reconcile_result = {"product_mapped": 0, "variants_mapped": 0, "product_id": None, "reason": str(exc)}
    setattr(obj, "_mapping_result", reconcile_result)
    return obj


def _normalize_order(db: Session, company_id: int, connection_id: int, data: dict) -> SallaOrder | None:
    external_id = _id(data.get("id") or data.get("order_id"))
    if not external_id:
        return None
    customer = _dict(data.get("customer"))
    obj = _upsert(db, SallaOrder, connection_id, external_id, {
        "company_id": company_id, "reference_id": str(data.get("reference_id")) if data.get("reference_id") is not None else None,
        "status": _code(data.get("status")), "payment_status": _code(data.get("payment_status")),
        "fulfillment_status": _code(data.get("fulfillment_status")), "order_type": _code(data.get("type")),
        "currency": data.get("currency"), "exchange_rate": _decimal(data.get("exchange_rate") or data.get("scope_exchange_rate")),
        "subtotal": _decimal(data.get("subtotal")), "discount": _decimal(data.get("discount")), "shipping": _decimal(data.get("shipping")),
        "tax": _decimal(data.get("tax")), "total": _decimal(data.get("total")), "cod_amount": _decimal(data.get("cash_on_delivery") or data.get("cod_amount")),
        "customer_id": _id(customer) or _id(data.get("customer_id")), "store_id": _id(data.get("store_id")), "created_at_salla": _dt(data.get("created_at")),
        "updated_at_salla": _dt(data.get("updated_at")), "urls": _dict(data.get("urls")), "payment_methods": _list(data.get("payment_methods")),
        "metadata_json": _dict(data.get("metadata")), "raw_payload": data,
    })
    db.flush()
    for item in _list(data.get("items") or data.get("order_items")):
        item = _dict(item)
        item_id = _id(item.get("id") or item.get("item_id"))
        if not item_id:
            continue
        product = _dict(item.get("product"))
        variant = _dict(item.get("sku")) if isinstance(item.get("sku"), dict) else {}
        _upsert(db, SallaOrderItem, connection_id, item_id, {
            "company_id": company_id, "order_id": obj.id, "product_external_id": _id(product) or _id(item.get("product_id")),
            "variant_external_id": _id(variant) or _id(item.get("sku_id")), "sku": item.get("sku") if isinstance(item.get("sku"), str) else item.get("sku_code"),
            "name": item.get("name") or product.get("name"), "quantity": _decimal(item.get("quantity")), "price": _decimal(item.get("price")),
            "subtotal": _decimal(item.get("subtotal")), "discount": _decimal(item.get("discount")), "tax": _decimal(item.get("tax")),
            "total": _decimal(item.get("total")), "cost_price": _decimal(item.get("cost_price")), "currency": item.get("currency") or data.get("currency"),
            "options": _list(item.get("options")), "taxes": _list(item.get("taxes")), "codes": _dict(item.get("codes")), "urls": _dict(item.get("urls")), "raw_payload": item,
        })
    if customer:
        _normalize_customer(db, company_id, connection_id, customer)
    return obj


def _normalize_shipment(db: Session, company_id: int, connection_id: int, data: dict) -> SallaShipment | None:
    external_id = _id(data.get("id") or data.get("shipment_id"))
    if not external_id:
        return None
    order_id = _id(data.get("order_id") or _dict(data.get("order")).get("id"))
    order = db.scalar(select(SallaOrder).where(SallaOrder.company_id == company_id, SallaOrder.connection_id == connection_id, SallaOrder.external_id == order_id)) if order_id else None
    courier = _dict(data.get("courier"))
    return _upsert(db, SallaShipment, connection_id, external_id, {
        "company_id": company_id, "order_id": order.id if order else None, "order_external_id": order_id,
        "order_reference_id": data.get("order_reference_id") or _dict(data.get("order")).get("reference_id"), "shipment_type": data.get("type"), "courier_id": _id(courier), "courier_name": courier.get("name"),
        "external_company_name": data.get("external_company_name"), "shipping_number": data.get("shipping_number"), "tracking_number": data.get("tracking_number"),
        "tracking_link": data.get("tracking_link"), "label": data.get("label"), "payment_method": _code(data.get("payment_method")), "source": data.get("source"),
        "status": _code(data.get("status")), "total": _decimal(data.get("total")), "cash_on_delivery": _decimal(data.get("cash_on_delivery")),
        "total_weight": _decimal(data.get("total_weight")), "international": data.get("international"), "trackable": data.get("trackable"),
        "packages": _list(data.get("packages")), "ship_from": _dict(data.get("ship_from")), "ship_to": _dict(data.get("ship_to")), "meta": _dict(data.get("meta")),
        "billing_account": _dict(data.get("billing_account")), "created_at_salla": _dt(data.get("created_at")), "raw_payload": data,
    })


def _normalize_invoice(db: Session, company_id: int, connection_id: int, data: dict) -> SallaInvoice | None:
    external_id = _id(data.get("id") or data.get("invoice_id"))
    if not external_id:
        return None
    order_id = _id(data.get("order_id") or _dict(data.get("order")).get("id"))
    order = db.scalar(select(SallaOrder).where(SallaOrder.connection_id == connection_id, SallaOrder.external_id == order_id)) if order_id else None
    return _upsert(db, SallaInvoice, connection_id, external_id, {
        "company_id": company_id, "order_id": order.id if order else None, "invoice_number": data.get("invoice_number"),
        "status": _code(data.get("status")), "subtotal": _decimal(data.get("subtotal")), "discount": _decimal(data.get("discount")),
        "tax": _decimal(data.get("tax")), "shipping": _decimal(data.get("shipping")), "total": _decimal(data.get("total")), "currency": data.get("currency"),
        "issue_date": _date(data.get("issue_date")), "due_date": _date(data.get("due_date")), "urls": _dict(data.get("urls")), "raw_payload": data,
    })


def normalize_salla_event(db: Session, event: IntegrationEvent) -> dict[str, int]:
    payload = event.payload
    if isinstance(payload, str):
        import json
        payload = json.loads(payload)
    payload = payload if isinstance(payload, dict) else {}
    data = _data(payload)
    key = _event_key(event.event_type)
    counters = {"orders": 0, "order_items": 0, "customers": 0, "products": 0, "variants": 0, "shipments": 0, "invoices": 0, "product_mapped": 0, "variants_mapped": 0}
    if key == "order":
        obj = _normalize_order(db, event.company_id, event.connection_id, data)
        counters["orders"] = int(obj is not None)
        counters["order_items"] = db.query(SallaOrderItem).filter(SallaOrderItem.company_id == event.company_id, SallaOrderItem.connection_id == event.connection_id, SallaOrderItem.order_id == obj.id).count() if obj else 0
    elif key == "customer":
        counters["customers"] = int(_normalize_customer(db, event.company_id, event.connection_id, data) is not None)
    elif key == "product":
        before = db.query(SallaProductVariant).filter(SallaProductVariant.connection_id == event.connection_id).count()
        obj = _normalize_product(db, event.company_id, event.connection_id, data)
        counters["products"] = int(obj is not None)
        counters["variants"] = db.query(SallaProductVariant).filter(SallaProductVariant.connection_id == event.connection_id).count() - before
        mapping_result = getattr(obj, "_mapping_result", {}) if obj else {}
        counters["product_mapped"] = int(mapping_result.get("product_mapped", 0))
        counters["variants_mapped"] = int(mapping_result.get("variants_mapped", 0))
    elif key == "shipment":
        counters["shipments"] = int(_normalize_shipment(db, event.company_id, event.connection_id, data) is not None)
    elif key == "invoice":
        counters["invoices"] = int(_normalize_invoice(db, event.company_id, event.connection_id, data) is not None)
    db.flush()
    return counters
