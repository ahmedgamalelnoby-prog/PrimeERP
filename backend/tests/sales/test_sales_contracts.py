from decimal import Decimal

from app.modules.sales.quotations.schemas import QuotationCreate
from app.modules.sales.sales_core.schemas import SalesOrderCreate


def test_sales_order_requires_lines():
    payload = SalesOrderCreate.model_validate({
        "company_id": 1,
        "customer_id": 2,
        "warehouse_id": 3,
        "order_number": "SO-001",
        "order_date": "2026-09-11",
        "lines": [{"item_id": 4, "quantity": "2", "unit_price": "100", "discount_amount": "10"}],
    })
    assert payload.lines[0].quantity == Decimal("2")


def test_quotation_requires_lines():
    payload = QuotationCreate.model_validate({
        "company_id": 1,
        "customer_id": 2,
        "quotation_number": "QT-001",
        "quotation_date": "2026-09-11",
        "lines": [{"item_id": 4, "quantity": "1", "unit_price": "50"}],
    })
    assert payload.lines[0].unit_price == Decimal("50")
