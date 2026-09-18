"""add configurable shipping carrier pricing engine

Revision ID: 20260918_shipping_pricing_engine
Revises: 20260917_saas_functional_hardening
"""
from alembic import op
import sqlalchemy as sa

revision = "20260918_shipping_pricing_engine"
down_revision = "20260917_saas_functional_hardening"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "shipping_pricing_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("carrier_id", sa.Integer(), sa.ForeignKey("shipping_carriers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date()),
        sa.Column("priority", sa.Integer(), server_default="100", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.CheckConstraint("priority >= 0", name="ck_shipping_pricing_profile_priority"),
        sa.CheckConstraint("effective_to IS NULL OR effective_to >= effective_from", name="ck_shipping_pricing_profile_dates"),
    )
    op.create_index("ix_shipping_pricing_profiles_company_id", "shipping_pricing_profiles", ["company_id"])
    op.create_index("ix_shipping_pricing_profiles_carrier_id", "shipping_pricing_profiles", ["carrier_id"])

    op.create_table(
        "shipping_pricing_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("profile_id", sa.Integer(), sa.ForeignKey("shipping_pricing_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rule_type", sa.String(40), nullable=False),
        sa.Column("basis", sa.String(30), server_default="order", nullable=False),
        sa.Column("zone_code", sa.String(80)),
        sa.Column("min_value", sa.Numeric(18, 6)),
        sa.Column("max_value", sa.Numeric(18, 6)),
        sa.Column("included_units", sa.Numeric(18, 6), server_default="0", nullable=False),
        sa.Column("fixed_amount", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("unit_amount", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("percent_rate", sa.Numeric(10, 6), server_default="0", nullable=False),
        sa.Column("minimum_amount", sa.Numeric(18, 4)),
        sa.Column("priority", sa.Integer(), server_default="100", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("description", sa.String(300)),
        sa.CheckConstraint("min_value IS NULL OR min_value >= 0", name="ck_shipping_rule_min"),
        sa.CheckConstraint("max_value IS NULL OR max_value >= 0", name="ck_shipping_rule_max"),
        sa.CheckConstraint("included_units >= 0", name="ck_shipping_rule_included"),
        sa.CheckConstraint("fixed_amount >= 0", name="ck_shipping_rule_fixed"),
        sa.CheckConstraint("unit_amount >= 0", name="ck_shipping_rule_unit"),
        sa.CheckConstraint("percent_rate >= 0 AND percent_rate <= 100", name="ck_shipping_rule_percent"),
        sa.CheckConstraint("minimum_amount IS NULL OR minimum_amount >= 0", name="ck_shipping_rule_minimum"),
        sa.CheckConstraint("priority >= 0", name="ck_shipping_rule_priority"),
    )
    op.create_index("ix_shipping_pricing_rules_profile_id", "shipping_pricing_rules", ["profile_id"])

    op.create_table(
        "shipping_shipment_costs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("shipment_id", sa.Integer(), sa.ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("profile_id", sa.Integer(), sa.ForeignKey("shipping_pricing_profiles.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("order_date", sa.Date()),
        sa.Column("shipment_date", sa.Date()),
        sa.Column("calculated_at", sa.Date(), nullable=False),
        sa.Column("base_shipping", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("cod_fee", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("cod_collected_fee", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("card_fee", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("remote_fee", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("rto_fee", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("exchange_fee", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("storage_fee", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("other_fees", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("minimum_adjustment", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("total_cost", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("calculation_breakdown", sa.Text()),
        sa.UniqueConstraint("shipment_id", name="uq_shipping_shipment_cost_shipment"),
    )
    op.create_index("ix_shipping_shipment_costs_profile_id", "shipping_shipment_costs", ["profile_id"])


def downgrade():
    op.drop_index("ix_shipping_shipment_costs_profile_id", table_name="shipping_shipment_costs")
    op.drop_table("shipping_shipment_costs")
    op.drop_index("ix_shipping_pricing_rules_profile_id", table_name="shipping_pricing_rules")
    op.drop_table("shipping_pricing_rules")
    op.drop_index("ix_shipping_pricing_profiles_carrier_id", table_name="shipping_pricing_profiles")
    op.drop_index("ix_shipping_pricing_profiles_company_id", table_name="shipping_pricing_profiles")
    op.drop_table("shipping_pricing_profiles")
