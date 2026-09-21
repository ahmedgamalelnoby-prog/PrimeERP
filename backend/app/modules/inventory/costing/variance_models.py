from sqlalchemy import Column, Integer, Numeric, String, DateTime, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.sql import func
from app.database.base import Base

class InventoryCostVariance(Base):
    __tablename__ = "inventory_cost_variances"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    warehouse_id = Column(Integer, ForeignKey("inventory_warehouses.id", ondelete="RESTRICT"), nullable=False, index=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=True, index=True)
    quantity = Column(Numeric(18,4), nullable=False)
    standard_unit_cost = Column(Numeric(18,6), nullable=False)
    actual_unit_cost = Column(Numeric(18,6), nullable=False)
    variance_value = Column(Numeric(18,4), nullable=False)
    basis = Column(String(30), nullable=False, default="standard_vs_actual")
    status = Column(String(20), nullable=False, default="calculated")
    journal_entry_id = Column(Integer, ForeignKey("accounting_journal_entries.id", ondelete="RESTRICT"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_inventory_cost_variance_qty"),
        CheckConstraint("standard_unit_cost >= 0 AND actual_unit_cost >= 0", name="ck_inventory_cost_variance_costs"),
        UniqueConstraint("company_id","item_id","warehouse_id","variant_id","basis","status","created_at", name="uq_inventory_cost_variance_snapshot"),
    )
