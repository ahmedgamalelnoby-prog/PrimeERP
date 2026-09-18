from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint

from app.database.base import Base


class ShippingShipmentCost(Base):
    __tablename__ = "shipping_shipment_costs"

    id = Column(Integer, primary_key=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    profile_id = Column(Integer, ForeignKey("shipping_pricing_profiles.id", ondelete="RESTRICT"), nullable=False, index=True)
    order_date = Column(Date)
    shipment_date = Column(Date)
    calculated_at = Column(DateTime, nullable=False)
    base_shipping = Column(Numeric(18, 4), server_default="0", nullable=False)
    cod_fee = Column(Numeric(18, 4), server_default="0", nullable=False)
    cod_collected_fee = Column(Numeric(18, 4), server_default="0", nullable=False)
    card_fee = Column(Numeric(18, 4), server_default="0", nullable=False)
    remote_fee = Column(Numeric(18, 4), server_default="0", nullable=False)
    rto_fee = Column(Numeric(18, 4), server_default="0", nullable=False)
    exchange_fee = Column(Numeric(18, 4), server_default="0", nullable=False)
    storage_fee = Column(Numeric(18, 4), server_default="0", nullable=False)
    other_fees = Column(Numeric(18, 4), server_default="0", nullable=False)
    minimum_adjustment = Column(Numeric(18, 4), server_default="0", nullable=False)
    total_cost = Column(Numeric(18, 4), server_default="0", nullable=False)
    calculation_breakdown = Column(Text)
