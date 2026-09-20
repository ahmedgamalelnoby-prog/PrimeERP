from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, Numeric, UniqueConstraint
from app.database.base import Base

class PurchaseReturnAllocation(Base):
    __tablename__ = "purchase_return_allocations"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    debit_note_line_id = Column(Integer, ForeignKey("purchase_lines.id", ondelete="CASCADE"), nullable=False, index=True)
    original_receipt_line_id = Column(Integer, ForeignKey("purchase_lines.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity = Column(Numeric(18, 4), nullable=False)
    unit_cost = Column(Numeric(18, 4), nullable=False)
    __table_args__ = (
        UniqueConstraint("debit_note_line_id", "original_receipt_line_id", name="uq_purchase_return_allocation_line"),
        CheckConstraint("quantity > 0", name="ck_purchase_return_allocation_quantity"),
        CheckConstraint("unit_cost >= 0", name="ck_purchase_return_allocation_unit_cost"),
    )
