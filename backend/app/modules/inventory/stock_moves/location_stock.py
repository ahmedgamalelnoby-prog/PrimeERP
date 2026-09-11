from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database.base import Base


class InventoryLocationStock(Base):
    __tablename__ = "inventory_location_stocks"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    location_id = Column(Integer, ForeignKey("inventory_locations.id", ondelete="RESTRICT"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity_on_hand = Column(Numeric(18, 4), nullable=False, default=0)
    quantity_reserved = Column(Numeric(18, 4), nullable=False, default=0)

    location = relationship("InventoryLocation")
    item = relationship("InventoryItem")

    __table_args__ = (
        UniqueConstraint("company_id", "location_id", "item_id", name="uq_inventory_location_stock"),
        CheckConstraint("quantity_on_hand >= 0", name="ck_inventory_location_stock_on_hand"),
        CheckConstraint("quantity_reserved >= 0", name="ck_inventory_location_stock_reserved"),
    )
