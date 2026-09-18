from sqlalchemy import Boolean, CheckConstraint, Column, Date, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint

from app.database.base import Base


class ShippingSettlementBatch(Base):
    __tablename__ = "shipping_settlement_batches"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    carrier_id = Column(Integer, ForeignKey("shipping_carriers.id", ondelete="RESTRICT"), nullable=False, index=True)
    reference = Column(String(100), nullable=False)
    settlement_date = Column(Date, nullable=False)
    gross_amount = Column(Numeric(18, 4), server_default="0", nullable=False)
    carrier_fees = Column(Numeric(18, 4), server_default="0", nullable=False)
    net_amount = Column(Numeric(18, 4), server_default="0", nullable=False)
    status = Column(String(20), server_default="open", nullable=False)
    notes = Column(Text)

    __table_args__ = (
        UniqueConstraint("company_id", "reference", name="uq_shipping_settlement_batch_reference"),
        CheckConstraint("gross_amount >= 0", name="ck_shipping_settlement_gross"),
        CheckConstraint("carrier_fees >= 0", name="ck_shipping_settlement_fees"),
        CheckConstraint("net_amount >= 0", name="ck_shipping_settlement_net"),
        CheckConstraint("status IN ('open','reconciled','cancelled')", name="ck_shipping_settlement_status"),
    )


class ShippingShipmentSettlement(Base):
    __tablename__ = "shipping_shipment_settlements"

    id = Column(Integer, primary_key=True)
    batch_id = Column(Integer, ForeignKey("shipping_settlement_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id", ondelete="RESTRICT"), nullable=False, unique=True)
    expected_amount = Column(Numeric(18, 4), server_default="0", nullable=False)
    collected_amount = Column(Numeric(18, 4), server_default="0", nullable=False)
    carrier_fee = Column(Numeric(18, 4), server_default="0", nullable=False)\n    cod_commission = Column(Numeric(18, 4), server_default="0", nullable=False)\n    withdrawal_fee = Column(Numeric(18, 4), server_default="0", nullable=False)\n    other_fee = Column(Numeric(18, 4), server_default="0", nullable=False)
    net_amount = Column(Numeric(18, 4), server_default="0", nullable=False)
    variance = Column(Numeric(18, 4), server_default="0", nullable=False)
    reconciled = Column(Boolean, server_default="false", nullable=False)

    __table_args__ = (
        CheckConstraint("expected_amount >= 0", name="ck_shipping_ship_settle_expected"),
        CheckConstraint("collected_amount >= 0", name="ck_shipping_ship_settle_collected"),
        CheckConstraint("carrier_fee >= 0", name="ck_shipping_ship_settle_fee"),
    )
