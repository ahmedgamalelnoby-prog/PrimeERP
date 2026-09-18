from sqlalchemy import Boolean, CheckConstraint, Column, Date, ForeignKey, Integer, Numeric, String, Text

from app.database.base import Base


class ShippingCarrier(Base):
    __tablename__ = "shipping_carriers"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(40), nullable=False)
    name = Column(String(150), nullable=False)
    api_base_url = Column(String(300))
    settlement_account_id = Column(Integer, ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=True, index=True)
    cash_account_id = Column(Integer, ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=True, index=True)
    fee_account_id = Column(Integer, ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=True, index=True)
    settlement_journal_id = Column(Integer, ForeignKey("accounting_journals.id", ondelete="RESTRICT"), nullable=True, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="RESTRICT"), nullable=True, index=True)
    is_active = Column(Boolean, server_default="true", nullable=False)


class ShippingMethod(Base):
    __tablename__ = "shipping_methods"
    id = Column(Integer, primary_key=True)
    carrier_id = Column(Integer, ForeignKey("shipping_carriers.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    payment_method = Column(String(20), nullable=False)
    payment_account_id = Column(Integer, ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=True, index=True)
    base_fee = Column(Numeric(18, 4), server_default="0", nullable=False)
    cod_fee_percent = Column(Numeric(8, 4), server_default="0", nullable=False)
    estimated_days = Column(Integer, server_default="1", nullable=False)

    __table_args__ = (
        CheckConstraint("payment_method IN ('prepaid','cod','mixed')", name="ck_shipping_method_payment"),
    )


class Shipment(Base):
    __tablename__ = "shipments"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    carrier_id = Column(Integer, ForeignKey("shipping_carriers.id", ondelete="RESTRICT"), nullable=False)
    method_id = Column(Integer, ForeignKey("shipping_methods.id", ondelete="RESTRICT"), nullable=False)
    sales_document_id = Column(Integer, ForeignKey("sales_documents.id", ondelete="RESTRICT"), nullable=True)
    tracking_no = Column(String(100), nullable=False, index=True)
    order_date = Column(Date)
    shipment_date = Column(Date)
    zone_code = Column(String(80))
    weight_kg = Column(Numeric(18, 6), server_default="0", nullable=False)
    pieces = Column(Numeric(18, 6), server_default="1", nullable=False)
    order_value = Column(Numeric(18, 4), server_default="0", nullable=False)
    cod_amount = Column(Numeric(18, 4), server_default="0", nullable=False)
    cod_collected = Column(Numeric(18, 4), server_default="0", nullable=False)
    card_amount = Column(Numeric(18, 4), server_default="0", nullable=False)
    remote_area = Column(Boolean, server_default="false", nullable=False)
    storage_days = Column(Numeric(18, 6), server_default="0", nullable=False)
    exchange_requested = Column(Boolean, server_default="false", nullable=False)
    status = Column(String(30), server_default="pending", nullable=False)
    shipping_fee = Column(Numeric(18, 4), server_default="0", nullable=False)
    customer_name = Column(String(200), nullable=False)
    phone = Column(String(50))
    address = Column(Text)
    notes = Column(Text)

    __table_args__ = (
        CheckConstraint("status IN ('pending','preparing','packing','picked_up','shipped','in_transit','out_for_delivery','delivering','returning','delivered','returned','cancelled')", name="ck_shipment_status"),
        CheckConstraint("cod_amount >= 0", name="ck_shipment_cod"),
        CheckConstraint("shipping_fee >= 0", name="ck_shipment_fee"),
    )
