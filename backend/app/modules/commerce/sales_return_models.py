from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, Numeric, UniqueConstraint
from app.database.base import Base


class SalesReturnAllocation(Base):
    __tablename__ = "sales_return_allocations"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    credit_note_line_id = Column(Integer, ForeignKey("sales_lines.id", ondelete="CASCADE"), nullable=False, index=True)
    original_delivery_line_id = Column(Integer, ForeignKey("sales_lines.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity = Column(Numeric(18, 4), nullable=False)
    unit_cost = Column(Numeric(18, 4), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default="CURRENT_TIMESTAMP")
    __table_args__ = (
        UniqueConstraint("credit_note_line_id", "original_delivery_line_id", name="uq_sales_return_allocation_line"),
        CheckConstraint("quantity > 0", name="ck_sales_return_allocation_quantity"),
        CheckConstraint("unit_cost >= 0", name="ck_sales_return_allocation_unit_cost"),
    )
