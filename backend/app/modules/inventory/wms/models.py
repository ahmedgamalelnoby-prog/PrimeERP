from sqlalchemy import Boolean, CheckConstraint, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class WMSOperation(Base):
    __tablename__ = "inventory_wms_operations"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    warehouse_id = Column(Integer, ForeignKey("inventory_warehouses.id", ondelete="RESTRICT"), nullable=False, index=True)
    operation_type = Column(String(20), nullable=False, index=True)
    reference = Column(String(100), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="draft", index=True)
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    posted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    lines = relationship("WMSOperationLine", back_populates="operation", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("company_id", "reference", name="uq_inventory_wms_operation_reference"),
        CheckConstraint("operation_type IN ('receiving','putaway','picking','packing','dispatch','cycle_count')", name="ck_inventory_wms_operation_type"),
        CheckConstraint("status IN ('draft','approved','in_progress','completed','cancelled')", name="ck_inventory_wms_operation_status"),
    )


class WMSOperationLine(Base):
    __tablename__ = "inventory_wms_operation_lines"

    id = Column(Integer, primary_key=True, index=True)
    operation_id = Column(Integer, ForeignKey("inventory_wms_operations.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=True, index=True)
    source_location_id = Column(Integer, ForeignKey("inventory_locations.id", ondelete="RESTRICT"), nullable=True)
    destination_location_id = Column(Integer, ForeignKey("inventory_locations.id", ondelete="RESTRICT"), nullable=True)
    quantity = Column(Numeric(18, 4), nullable=False)
    processed_quantity = Column(Numeric(18, 4), nullable=False, default=0)
    unit_cost = Column(Numeric(18, 4), nullable=False, default=0)
    lot_number = Column(String(100), nullable=True, index=True)
    serial_number = Column(String(100), nullable=True, index=True)
    expiry_date = Column(Date, nullable=True, index=True)
    barcode = Column(String(100), nullable=True, index=True)
    stock_move_id = Column(Integer, ForeignKey("inventory_stock_moves.id", ondelete="RESTRICT"), nullable=True, unique=True)
    reservation_id = Column(Integer, ForeignKey("inventory_reservations.id", ondelete="RESTRICT"), nullable=True, index=True)
    count_expected = Column(Numeric(18, 4), nullable=True)
    count_actual = Column(Numeric(18, 4), nullable=True)

    operation = relationship("WMSOperation", back_populates="lines")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_inventory_wms_line_quantity"),
        CheckConstraint("processed_quantity >= 0 AND processed_quantity <= quantity", name="ck_inventory_wms_line_processed"),
        CheckConstraint("unit_cost >= 0", name="ck_inventory_wms_line_cost"),
        CheckConstraint("serial_number IS NULL OR quantity = 1", name="ck_inventory_wms_serial_one"),
    )


class InventoryTrackingUnit(Base):
    __tablename__ = "inventory_tracking_units"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=True, index=True)
    warehouse_id = Column(Integer, ForeignKey("inventory_warehouses.id", ondelete="RESTRICT"), nullable=False, index=True)
    location_id = Column(Integer, ForeignKey("inventory_locations.id", ondelete="RESTRICT"), nullable=False, index=True)
    lot_number = Column(String(100), nullable=True, index=True)
    serial_number = Column(String(100), nullable=True, index=True)
    expiry_date = Column(Date, nullable=True, index=True)
    barcode = Column(String(100), nullable=True, index=True)
    quantity = Column(Numeric(18, 4), nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_inventory_tracking_unit_quantity"),
        UniqueConstraint("company_id", "item_id", "variant_id", "location_id", "lot_number", "serial_number", name="uq_inventory_tracking_unit_identity"),
    )
