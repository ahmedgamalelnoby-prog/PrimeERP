from app.modules.platform.customers.models import Customer


def test_customer_table_contract():
    assert Customer.__tablename__ == "sales_customers"
    assert "company_id" in Customer.__table__.c
    assert "code" in Customer.__table__.c
    assert "credit_limit" in Customer.__table__.c
