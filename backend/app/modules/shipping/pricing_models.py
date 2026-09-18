from sqlalchemy import Boolean, CheckConstraint, Column, Date, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint

from app.database.base import Base


class ShippingPricingProfile(Base):
    __tablename__ = "shipping_pricing_profiles"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    carrier_id = Column(Integer, ForeignKey("shipping_carriers.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date)
    priority = Column(Integer, server_default="100", nullable=False)
    is_active = Column(Boolean, server_default="true", nullable=False)
    notes = Column(Text)

    __table_args__ = (
        CheckConstraint("priority >= 0", name="ck_shipping_pricing_profile_priority"),
        CheckConstraint("effective_to IS NULL OR effective_to >= effective_from", name="ck_shipping_pricing_profile_dates"),
    )


class ShippingPricingRule(Base):
    __tablename__ = "shipping_pricing_rules"

    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("shipping_pricing_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_type = Column(String(40), nullable=False)
    basis = Column(String(30), nullable=False, server_default="order")
    zone_code = Column(String(80))
    min_value = Column(Numeric(18, 6))
    max_value = Column(Numeric(18, 6))
    included_units = Column(Numeric(18, 6), server_default="0", nullable=False)
    fixed_amount = Column(Numeric(18, 4), server_default="0", nullable=False)
    unit_amount = Column(Numeric(18, 4), server_default="0", nullable=False)
    percent_rate = Column(Numeric(10, 6), server_default="0", nullable=False)
    minimum_amount = Column(Numeric(18, 4))
    priority = Column(Integer, server_default="100", nullable=False)
    is_active = Column(Boolean, server_default="true", nullable=False)
    description = Column(String(300))

    __table_args__ = (
        CheckConstraint("min_value IS NULL OR min_value >= 0", name="ck_shipping_rule_min"),
        CheckConstraint("max_value IS NULL OR max_value >= 0", name="ck_shipping_rule_max"),
        CheckConstraint("included_units >= 0", name="ck_shipping_rule_included"),
        CheckConstraint("fixed_amount >= 0", name="ck_shipping_rule_fixed"),
        CheckConstraint("unit_amount >= 0", name="ck_shipping_rule_unit"),
        CheckConstraint("percent_rate >= 0 AND percent_rate <= 100", name="ck_shipping_rule_percent"),
        CheckConstraint("minimum_amount IS NULL OR minimum_amount >= 0", name="ck_shipping_rule_minimum"),
        CheckConstraint("priority >= 0", name="ck_shipping_rule_priority"),
    )
