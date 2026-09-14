from sqlalchemy import CheckConstraint, Column, ForeignKey, Index, Integer, Numeric
from sqlalchemy.orm import relationship

from app.database.base import Base


class InventoryLocationStock(Base):
    __tablename__ = "inventory_location_stocks"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    location_id = Column(Integer, ForeignKey("inventory_locations.id", ondelete="RESTRICT"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=True, index=True)
    quantity_on_hand = Column(Numeric(18, 4), nullable=False, default=0)
    quantity_reserved = Column(Numeric(18, 4), nullable=False, default=0)

    location = relationship("InventoryLocation")
    item = relationship("InventoryItem")
    variant = relationship("ProductVariant")

    __table_args__ = (
        Index("uq_inventory_location_stock_variant", "company_id", "location_id", "item_id", "variant_id", unique=True, postgresql_where=variant_id.is_not(None)),
        Index("uq_inventory_location_stock_product", "company_id", "location_id", "item_id", unique=True, postgresql_where=variant_id.is_(None)),
        CheckConstraint("quantity_on_hand >= 0", name="ck_inventory_location_stock_on_hand"),
        CheckConstraint("quantity_reserved >= 0", name="ck_inventory_location_stock_reserved"),
    )
