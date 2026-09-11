from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.database.base import Base


class InventoryStockMove(Base):
    __tablename__ = "inventory_stock_moves"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    source_location_id = Column(Integer, ForeignKey("inventory_locations.id", ondelete="RESTRICT"), nullable=True, index=True)
    destination_location_id = Column(Integer, ForeignKey("inventory_locations.id", ondelete="RESTRICT"), nullable=True, index=True)
    quantity = Column(Numeric(18, 4), nullable=False)
    unit_cost = Column(Numeric(18, 4), nullable=False, default=0)
    movement_type = Column(String(30), nullable=False)
    status = Column(String(20), nullable=False, default="draft")
    reference = Column(String(100), nullable=True, index=True)
    source_module = Column(String(80), nullable=True)
    source_entity = Column(String(80), nullable=True)
    source_id = Column(String(80), nullable=True)
    notes = Column(Text, nullable=True)

    item = relationship("InventoryItem")
    source_location = relationship("InventoryLocation", foreign_keys=[source_location_id])
    destination_location = relationship("InventoryLocation", foreign_keys=[destination_location_id])

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_inventory_stock_move_quantity"),
        CheckConstraint("unit_cost >= 0", name="ck_inventory_stock_move_unit_cost"),
        CheckConstraint("movement_type IN ('receipt','issue','transfer','adjustment','opening','return')", name="ck_inventory_stock_move_type"),
        CheckConstraint("status IN ('draft','posted','cancelled','reversed')", name="ck_inventory_stock_move_status"),
        CheckConstraint("source_location_id IS NOT NULL OR destination_location_id IS NOT NULL", name="ck_inventory_stock_move_endpoint"),
        CheckConstraint("source_location_id IS NULL OR destination_location_id IS NULL OR source_location_id <> destination_location_id", name="ck_inventory_stock_move_distinct_endpoints"),
    )


class InventoryCostLayer(Base):
    __tablename__ = "inventory_cost_layers"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    warehouse_id = Column(Integer, ForeignKey("inventory_warehouses.id", ondelete="RESTRICT"), nullable=False, index=True)
    receipt_move_id = Column(Integer, ForeignKey("inventory_stock_moves.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity_remaining = Column(Numeric(18, 4), nullable=False)
    unit_cost = Column(Numeric(18, 4), nullable=False)

    receipt_move = relationship("InventoryStockMove")

    __table_args__ = (
        CheckConstraint("quantity_remaining >= 0", name="ck_inventory_cost_layer_quantity"),
        CheckConstraint("unit_cost >= 0", name="ck_inventory_cost_layer_unit_cost"),
    )
