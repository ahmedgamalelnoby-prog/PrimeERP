from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.database.base import Base


class InventoryTransfer(Base):
    __tablename__ = "inventory_transfers"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    source_warehouse_id = Column(Integer, ForeignKey("inventory_warehouses.id", ondelete="RESTRICT"), nullable=False)
    destination_warehouse_id = Column(Integer, ForeignKey("inventory_warehouses.id", ondelete="RESTRICT"), nullable=False)
    reference = Column(String(100), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="draft", index=True)
    notes = Column(Text, nullable=True)

    source_warehouse = relationship("InventoryWarehouse", foreign_keys=[source_warehouse_id])
    destination_warehouse = relationship("InventoryWarehouse", foreign_keys=[destination_warehouse_id])
    lines = relationship("InventoryTransferLine", back_populates="transfer", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("source_warehouse_id <> destination_warehouse_id", name="ck_inventory_transfer_distinct_warehouses"),
        CheckConstraint("status IN ('draft','requested','approved','shipped','received','cancelled')", name="ck_inventory_transfer_status"),
    )


class InventoryTransferLine(Base):
    __tablename__ = "inventory_transfer_lines"

    id = Column(Integer, primary_key=True, index=True)
    transfer_id = Column(Integer, ForeignKey("inventory_transfers.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    source_location_id = Column(Integer, ForeignKey("inventory_locations.id", ondelete="RESTRICT"), nullable=False)
    destination_location_id = Column(Integer, ForeignKey("inventory_locations.id", ondelete="RESTRICT"), nullable=False)
    quantity = Column(Numeric(18, 4), nullable=False)
    unit_cost = Column(Numeric(18, 4), nullable=False, default=0)

    transfer = relationship("InventoryTransfer", back_populates="lines")
    item = relationship("InventoryItem")
    source_location = relationship("InventoryLocation", foreign_keys=[source_location_id])
    destination_location = relationship("InventoryLocation", foreign_keys=[destination_location_id])

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_inventory_transfer_line_quantity"),
        CheckConstraint("unit_cost >= 0", name="ck_inventory_transfer_line_cost"),
        CheckConstraint("source_location_id <> destination_location_id", name="ck_inventory_transfer_line_locations"),
    )
