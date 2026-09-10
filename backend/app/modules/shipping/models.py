"""Shipping & Logistics domain models."""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base


class ShippingProvider(Base):
    __tablename__ = "shipping_providers"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(150), nullable=False)
    country_code = Column(String(2), nullable=False, default="EG")
    website = Column(String(255), nullable=True)
    api_enabled = Column(Boolean, nullable=False, default=False)
    active = Column(Boolean, nullable=False, default=True, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    services = relationship("ShippingProviderService", back_populates="provider", cascade="all, delete-orphan")
    payment_profiles = relationship("ShippingPaymentProfile", back_populates="provider", cascade="all, delete-orphan")
    shipments = relationship("Shipment", back_populates="provider")
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_shipping_provider_tenant_code"),)


class ShippingProviderService(Base):
    __tablename__ = "shipping_provider_services"
    id = Column(Integer, primary_key=True)
    provider_id = Column(Integer, ForeignKey("shipping_providers.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(150), nullable=False)
    service_type = Column(String(30), nullable=False, default="standard")
    supports_cod = Column(Boolean, nullable=False, default=False)
    supports_returns = Column(Boolean, nullable=False, default=True)
    active = Column(Boolean, nullable=False, default=True)
    provider = relationship("ShippingProvider", back_populates="services")
    __table_args__ = (UniqueConstraint("provider_id", "code", name="uq_shipping_service_provider_code"),)


class ShippingPaymentProfile(Base):
    __tablename__ = "shipping_payment_profiles"
    id = Column(Integer, primary_key=True)
    provider_id = Column(Integer, ForeignKey("shipping_providers.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    payment_method = Column(String(30), nullable=False)
    billing_cycle = Column(String(30), nullable=False, default="per_shipment")
    cod_enabled = Column(Boolean, nullable=False, default=False)
    cod_fee_type = Column(String(20), nullable=True)
    cod_fee_value = Column(Numeric(18, 4), nullable=True)
    settlement_cycle = Column(String(30), nullable=False, default="contractual")
    settlement_percent = Column(Numeric(7, 4), nullable=True)
    currency_code = Column(String(3), nullable=False, default="EGP")
    active = Column(Boolean, nullable=False, default=True)
    notes = Column(Text, nullable=True)
    provider = relationship("ShippingProvider", back_populates="payment_profiles")


class ShippingRateCard(Base):
    __tablename__ = "shipping_rate_cards"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_id = Column(Integer, ForeignKey("shipping_providers.id", ondelete="CASCADE"), nullable=False, index=True)
    service_id = Column(Integer, ForeignKey("shipping_provider_services.id", ondelete="CASCADE"), nullable=True)
    zone_code = Column(String(50), nullable=False)
    min_weight_kg = Column(Numeric(12, 3), nullable=False, default=0)
    max_weight_kg = Column(Numeric(12, 3), nullable=True)
    base_fee = Column(Numeric(18, 2), nullable=False, default=0)
    extra_kg_fee = Column(Numeric(18, 2), nullable=False, default=0)
    return_fee = Column(Numeric(18, 2), nullable=False, default=0)
    insurance_percent = Column(Numeric(7, 4), nullable=False, default=0)
    active = Column(Boolean, nullable=False, default=True)


class Shipment(Base):
    __tablename__ = "shipments"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=True, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="RESTRICT"), nullable=True, index=True)
    transaction_id = Column(Integer, ForeignKey("business_transactions.id", ondelete="SET NULL"), nullable=True, index=True)
    source_module = Column(String(80), nullable=True)
    source_entity = Column(String(100), nullable=True)
    source_id = Column(Integer, nullable=True)
    provider_id = Column(Integer, ForeignKey("shipping_providers.id", ondelete="RESTRICT"), nullable=False, index=True)
    service_id = Column(Integer, ForeignKey("shipping_provider_services.id", ondelete="SET NULL"), nullable=True)
    reference = Column(String(100), nullable=False, index=True)
    external_id = Column(String(150), nullable=True, index=True)
    tracking_number = Column(String(150), nullable=True, index=True)
    status = Column(String(30), nullable=False, default="draft", index=True)
    payment_method = Column(String(30), nullable=False, default="prepaid")
    cod_amount = Column(Numeric(18, 2), nullable=False, default=0)
    shipping_fee = Column(Numeric(18, 2), nullable=False, default=0)
    cod_fee = Column(Numeric(18, 2), nullable=False, default=0)
    other_fee = Column(Numeric(18, 2), nullable=False, default=0)
    weight_kg = Column(Numeric(12, 3), nullable=True)
    volumetric_weight_kg = Column(Numeric(12, 3), nullable=True)
    customer_name = Column(String(200), nullable=False)
    customer_phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    country_code = Column(String(2), nullable=False, default="EG")
    shipped_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    returned_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, onupdate=func.now())
    provider = relationship("ShippingProvider", back_populates="shipments")
    events = relationship("ShipmentEvent", back_populates="shipment", cascade="all, delete-orphan")


class ShipmentEvent(Base):
    __tablename__ = "shipment_events"
    id = Column(Integer, primary_key=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(30), nullable=False)
    event_code = Column(String(80), nullable=True)
    description = Column(Text, nullable=True)
    event_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    raw_payload = Column(Text, nullable=True)
    shipment = relationship("Shipment", back_populates="events")


class ShippingSettlement(Base):
    __tablename__ = "shipping_settlements"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_id = Column(Integer, ForeignKey("shipping_providers.id", ondelete="RESTRICT"), nullable=False, index=True)
    settlement_reference = Column(String(150), nullable=False)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)
    gross_cod = Column(Numeric(18, 2), nullable=False, default=0)
    shipping_fees = Column(Numeric(18, 2), nullable=False, default=0)
    cod_fees = Column(Numeric(18, 2), nullable=False, default=0)
    adjustments = Column(Numeric(18, 2), nullable=False, default=0)
    net_amount = Column(Numeric(18, 2), nullable=False, default=0)
    status = Column(String(30), nullable=False, default="draft", index=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    __table_args__ = (UniqueConstraint("tenant_id", "settlement_reference", name="uq_shipping_settlement_reference"),)
