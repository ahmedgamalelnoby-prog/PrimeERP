from sqlalchemy import Boolean, CheckConstraint, Column, Date, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint

from app.database.base import Base


class ShippingOrderStatus(Base):
    __tablename__ = "shipping_order_statuses"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(120), nullable=False)
    name_ar = Column(String(120), nullable=True)
    parent_code = Column(String(50))
    sort_order = Column(Integer, server_default="0", nullable=False)
    is_active = Column(Boolean, server_default="true", nullable=False)
    financial_actions = Column(Text, server_default="[]", nullable=False)
    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_shipping_order_status_company_code"),
        CheckConstraint("sort_order >= 0", name="ck_shipping_order_status_sort"),
    )


class ShippingStatusHistory(Base):
    __tablename__ = "shipping_status_histories"
    id = Column(Integer, primary_key=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False, index=True)
    from_status = Column(String(50))
    to_status = Column(String(50), nullable=False)
    changed_on = Column(Date, nullable=False)
    note = Column(Text)


class ShippingFinancialEvent(Base):
    __tablename__ = "shipping_financial_events"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    carrier_id = Column(Integer, ForeignKey("shipping_carriers.id", ondelete="RESTRICT"), nullable=False, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False, index=True)
    event_key = Column(String(80), nullable=False)
    event_type = Column(String(50), nullable=False)
    event_date = Column(Date, nullable=False, index=True)
    amount = Column(Numeric(18, 4), server_default="0", nullable=False)
    debit_role = Column(String(50), nullable=False)
    credit_role = Column(String(50), nullable=False)
    source_status = Column(String(50), nullable=False)
    is_reversal = Column(Boolean, server_default="false", nullable=False)
    description = Column(Text)
    __table_args__ = (
        UniqueConstraint("shipment_id", "event_key", name="uq_shipping_fin_event_shipment_key"),
        CheckConstraint("amount >= 0", name="ck_shipping_fin_event_amount"),
    )
