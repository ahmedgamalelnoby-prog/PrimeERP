from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.database.base import Base


class InventoryReservation(Base):
    __tablename__ = "inventory_reservations"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=True, index=True)
    location_id = Column(Integer, ForeignKey("inventory_locations.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity = Column(Numeric(18, 4), nullable=False)
    status = Column(String(20), nullable=False, default="active", index=True)
    source_module = Column(String(80), nullable=False)
    source_entity = Column(String(80), nullable=False)
    source_id = Column(String(80), nullable=False)
    reference = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)

    item = relationship("InventoryItem")
    variant = relationship("ProductVariant")
    location = relationship("InventoryLocation")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_inventory_reservation_quantity"),
        CheckConstraint("status IN ('active','released','consumed','cancelled')", name="ck_inventory_reservation_status"),
    )
