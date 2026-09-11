from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.modules.platform.customers.models import Customer


class SalesOrder(Base):
    __tablename__ = "sales_orders"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("sales_customers.id", ondelete="RESTRICT"), nullable=False, index=True)
    warehouse_id = Column(Integer, ForeignKey("inventory_warehouses.id", ondelete="RESTRICT"), nullable=False, index=True)
    order_number = Column(String(50), nullable=False)
    order_date = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="draft", index=True)
    total_amount = Column(Numeric(18, 4), nullable=False, default=0)
    reference = Column(String(100))
    notes = Column(Text)

    customer = relationship(Customer)

    __table_args__ = (
        CheckConstraint("status IN ('draft','confirmed','partially_shipped','shipped','cancelled')", name="ck_sales_order_status"),
        CheckConstraint("total_amount >= 0", name="ck_sales_order_total"),
    )


__all__ = ["SalesOrder"]
