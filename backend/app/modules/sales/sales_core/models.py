from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database.base import Base


class SalesCustomer(Base):
    __tablename__ = "sales_customers"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    tax_id = Column(String(100))
    email = Column(String(200))
    phone = Column(String(50))
    address = Column(Text)
    credit_limit = Column(String(40), nullable=False, default="0")
    is_active = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="ck_sales_customer_name"),
        CheckConstraint("length(trim(code)) > 0", name="ck_sales_customer_code"),
    )


class SalesOrder(Base):
    __tablename__ = "sales_orders"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("sales_customers.id", ondelete="RESTRICT"), nullable=False, index=True)
    warehouse_id = Column(Integer, ForeignKey("inventory_warehouses.id", ondelete="RESTRICT"), nullable=False, index=True)
    order_number = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="draft", index=True)
    total_amount = Column(String(40), nullable=False, default="0")
    reference = Column(String(100))
    notes = Column(Text)

    customer = relationship("SalesCustomer")

    __table_args__ = (
        CheckConstraint("status IN ('draft','confirmed','partially_shipped','shipped','cancelled')", name="ck_sales_order_status"),
    )


__all__ = ["SalesCustomer", "SalesOrder"]
