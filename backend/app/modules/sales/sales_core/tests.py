from app.modules.sales.sales_core.models import SalesOrder


def test_sales_order_contract():
    assert SalesOrder.__tablename__ == "sales_orders"
    assert "customer_id" in SalesOrder.__table__.c
    assert "warehouse_id" in SalesOrder.__table__.c
    assert "status" in SalesOrder.__table__.c
