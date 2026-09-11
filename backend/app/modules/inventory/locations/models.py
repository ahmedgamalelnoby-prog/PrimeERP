from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database.base import Base


class InventoryLocation(Base):
    __tablename__ = "inventory_locations"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    warehouse_id = Column(Integer, ForeignKey("inventory_warehouses.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("inventory_locations.id", ondelete="RESTRICT"), nullable=True, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(150), nullable=False)
    location_type = Column(String(30), nullable=False, default="storage")
    is_virtual = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    description = Column(Text, nullable=True)

    warehouse = relationship("InventoryWarehouse")
    parent = relationship("InventoryLocation", remote_side=[id], back_populates="children")
    children = relationship("InventoryLocation", back_populates="parent")

    __table_args__ = (
        UniqueConstraint("warehouse_id", "code", name="uq_inventory_location_warehouse_code"),
        CheckConstraint(
            "location_type IN ('storage','receiving','shipping','quarantine','damaged','transit','virtual')",
            name="ck_inventory_location_type",
        ),
    )
