from datetime import date
from decimal import Decimal

from app.modules.integrations.salla_service import _data, _date, _decimal, _event_key
from app.modules.integrations.salla_models import SallaCustomer, SallaInvoice, SallaOrder, SallaOrderItem, SallaProduct, SallaProductVariant, SallaShipment


def test_salla_event_types_are_normalized_by_domain():
    assert _event_key("order.created") == "order"
    assert _event_key("order.updated") == "order"
    assert _event_key("product.updated") == "product"
    assert _event_key("customer.created") == "customer"
    assert _event_key("shipment.status.updated") == "shipment"
    assert _event_key("order.invoice.created") == "invoice"


def test_salla_value_helpers_are_tolerant():
    assert _decimal({"amount": "123.45"}) == Decimal("123.45")
    assert _decimal("bad-number") is None
    assert _date("2026-09-13T18:00:00Z") == date(2026, 9, 13)
    assert _data({"data": {"id": 10}}) == {"id": 10}
    assert _data({"id": 10}) == {"id": 10}


def test_salla_tables_keep_normalized_columns_and_raw_payload():
    for model, required in {
        SallaOrder: {"external_id", "reference_id", "status", "total", "payment_methods", "raw_payload"},
        SallaOrderItem: {"external_id", "order_id", "product_external_id", "variant_external_id", "quantity", "taxes", "raw_payload"},
        SallaCustomer: {"external_id", "first_name", "mobile", "email", "location", "groups", "raw_payload"},
        SallaProduct: {"external_id", "sku", "gtin", "price", "tax", "quantity", "options", "raw_payload"},
        SallaProductVariant: {"external_id", "product_id", "sku", "barcode", "stock", "option_values", "raw_payload"},
        SallaShipment: {"external_id", "order_id", "tracking_number", "tracking_link", "payment_method", "status", "ship_to", "raw_payload"},
        SallaInvoice: {"external_id", "order_id", "invoice_number", "tax", "total", "issue_date", "raw_payload"},
    }.items():
        assert required.issubset(model.__table__.columns.keys())
