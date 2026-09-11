from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, Integer, Numeric, String, Text
from app.database.base import Base


class Customer(Base):
    __tablename__ = "sales_customers"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    tax_id = Column(String(100))
    email = Column(String(200))
    phone = Column(String(50))
    address = Column(Text)
    credit_limit = Column(Numeric(18, 4), nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="ck_sales_customer_name"),
        CheckConstraint("length(trim(code)) > 0", name="ck_sales_customer_code"),
        CheckConstraint("credit_limit >= 0", name="ck_sales_customer_credit_limit"),
    )


__all__ = ["Customer"]
