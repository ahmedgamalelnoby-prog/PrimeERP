from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from app.database.base import Base
from app.modules.platform.customers.models import Customer
from app.modules.inventory.items.models import InventoryItem


class SalesQuotation(Base):
    __tablename__ = "sales_quotations"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("sales_customers.id", ondelete="RESTRICT"), nullable=False, index=True)
    quotation_number = Column(String(50), nullable=False)
    quotation_date = Column(String(20), nullable=False)
    valid_until = Column(String(20))
    status = Column(String(20), nullable=False, default="draft", index=True)
    total_amount = Column(Numeric(18, 4), nullable=False, default=0)
    notes = Column(Text)
    customer = relationship(Customer)
    lines = relationship("SalesQuotationLine", back_populates="quotation", cascade="all, delete-orphan", order_by="SalesQuotationLine.id")
    __table_args__ = (
        CheckConstraint("status IN ('draft','sent','accepted','rejected','expired','cancelled')", name="ck_sales_quotation_status"),
        CheckConstraint("total_amount >= 0", name="ck_sales_quotation_total"),
    )


class SalesQuotationLine(Base):
    __tablename__ = "sales_quotation_lines"
    id = Column(Integer, primary_key=True, index=True)
    quotation_id = Column(Integer, ForeignKey("sales_quotations.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity = Column(Numeric(18, 4), nullable=False)
    unit_price = Column(Numeric(18, 4), nullable=False)
    discount_amount = Column(Numeric(18, 4), nullable=False, default=0)
    line_total = Column(Numeric(18, 4), nullable=False, default=0)
    quotation = relationship(SalesQuotation, back_populates="lines")
    item = relationship(InventoryItem)
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_sales_quotation_line_qty"),
        CheckConstraint("unit_price >= 0", name="ck_sales_quotation_line_price"),
        CheckConstraint("discount_amount >= 0", name="ck_sales_quotation_line_discount"),
        CheckConstraint("line_total >= 0", name="ck_sales_quotation_line_total"),
    )
