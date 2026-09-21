from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class InventoryReservation(Base):
    __tablename__ = "inventory_reservations"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=True, index=True)
    location_id = Column(Integer, ForeignKey("inventory_locations.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity = Column(Numeric(18, 4), nullable=False)
    consumed_quantity = Column(Numeric(18, 4), nullable=False, default=0)
    status = Column(String(20), nullable=False, default="active", index=True)
    source_module = Column(String(80), nullable=False)
    source_entity = Column(String(80), nullable=False)
    source_id = Column(String(80), nullable=False)
    reference = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)

    item = relationship("InventoryItem")
    variant = relationship("ProductVariant")
    location = relationship("InventoryLocation")
    consumptions = relationship("InventoryReservationConsumption", back_populates="reservation", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_inventory_reservation_quantity"),
        CheckConstraint("consumed_quantity >= 0 AND consumed_quantity <= quantity", name="ck_inventory_reservation_consumed_quantity"),
        CheckConstraint("status IN ('active','released','consumed','cancelled')", name="ck_inventory_reservation_status"),
    )


class InventoryReservationConsumption(Base):
    __tablename__ = "inventory_reservation_consumptions"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    reservation_id = Column(Integer, ForeignKey("inventory_reservations.id", ondelete="CASCADE"), nullable=False, index=True)
    quantity = Column(Numeric(18, 4), nullable=False)
    source_module = Column(String(80), nullable=False)
    source_entity = Column(String(80), nullable=False)
    source_id = Column(String(120), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    reservation = relationship("InventoryReservation", back_populates="consumptions")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_inventory_reservation_consumption_quantity"),
        UniqueConstraint("company_id", "reservation_id", "source_module", "source_entity", "source_id", name="uq_inventory_reservation_consumption_source"),
    )
