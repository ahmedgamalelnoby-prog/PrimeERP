from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.database.base import Base


class InventoryAdjustment(Base):
    __tablename__ = "inventory_adjustments"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=True, index=True)
    location_id = Column(Integer, ForeignKey("inventory_locations.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity = Column(Numeric(18, 4), nullable=False)
    direction = Column(String(10), nullable=False)
    unit_cost = Column(Numeric(18, 4), nullable=False, default=0)
    reason = Column(String(100), nullable=False)
    reference = Column(String(100), nullable=True, index=True)
    status = Column(String(20), nullable=False, default="draft", index=True)
    notes = Column(Text, nullable=True)

    item = relationship("InventoryItem")
    variant = relationship("ProductVariant")
    location = relationship("InventoryLocation")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_inventory_adjustment_quantity"),
        CheckConstraint("unit_cost >= 0", name="ck_inventory_adjustment_unit_cost"),
        CheckConstraint("direction IN ('increase','decrease')", name="ck_inventory_adjustment_direction"),
        CheckConstraint("status IN ('draft','approved','posted','cancelled')", name="ck_inventory_adjustment_status"),
    )
