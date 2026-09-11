from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, Integer, Numeric, String, Text
from app.database.base import Base


class ShippingCarrier(Base):
    __tablename__ = "shipping_carriers"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(40), nullable=False)
    name = Column(String(150), nullable=False)
    api_base_url = Column(String(300))
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
    status = Column(String(30), server_default="pending", nullable=False)
    cod_amount = Column(Numeric(18, 4), server_default="0", nullable=False)
    shipping_fee = Column(Numeric(18, 4), server_default="0", nullable=False)
    customer_name = Column(String(200), nullable=False)
    phone = Column(String(50))
    address = Column(Text)
    notes = Column(Text)

    __table_args__ = (
        CheckConstraint("status IN ('pending','picked_up','in_transit','out_for_delivery','delivered','returned','cancelled')", name="ck_shipment_status"),
        CheckConstraint("cod_amount >= 0", name="ck_shipment_cod"),
    )
