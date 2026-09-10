"""Add Shipping & Logistics foundation.

Revision ID: 20260911shipping
Revises: 20260831legal
"""
from alembic import op
import sqlalchemy as sa

revision = "20260911shipping"
down_revision = "20260831legal"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("shipping_providers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(50), nullable=False), sa.Column("name", sa.String(150), nullable=False),
        sa.Column("country_code", sa.String(2), nullable=False, server_default="EG"), sa.Column("website", sa.String(255)),
        sa.Column("api_enabled", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("notes", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_shipping_provider_tenant_code"))
    op.create_index("ix_shipping_providers_tenant_id", "shipping_providers", ["tenant_id"])
    op.create_index("ix_shipping_providers_active", "shipping_providers", ["active"])

    op.create_table("shipping_provider_services",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("provider_id", sa.Integer(), sa.ForeignKey("shipping_providers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(50), nullable=False), sa.Column("name", sa.String(150), nullable=False), sa.Column("service_type", sa.String(30), nullable=False, server_default="standard"),
        sa.Column("supports_cod", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("supports_returns", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.UniqueConstraint("provider_id", "code", name="uq_shipping_service_provider_code"))

    op.create_table("shipping_payment_profiles",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("provider_id", sa.Integer(), sa.ForeignKey("shipping_providers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(150), nullable=False), sa.Column("payment_method", sa.String(30), nullable=False), sa.Column("billing_cycle", sa.String(30), nullable=False, server_default="per_shipment"),
        sa.Column("cod_enabled", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("cod_fee_type", sa.String(20)), sa.Column("cod_fee_value", sa.Numeric(18,4)),
        sa.Column("settlement_cycle", sa.String(30), nullable=False, server_default="contractual"), sa.Column("settlement_percent", sa.Numeric(7,4)),
        sa.Column("currency_code", sa.String(3), nullable=False, server_default="EGP"), sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("notes", sa.Text()))

    op.create_table("shipping_rate_cards",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider_id", sa.Integer(), sa.ForeignKey("shipping_providers.id", ondelete="CASCADE"), nullable=False), sa.Column("service_id", sa.Integer(), sa.ForeignKey("shipping_provider_services.id", ondelete="CASCADE")),
        sa.Column("zone_code", sa.String(50), nullable=False), sa.Column("min_weight_kg", sa.Numeric(12,3), nullable=False, server_default="0"), sa.Column("max_weight_kg", sa.Numeric(12,3)),
        sa.Column("base_fee", sa.Numeric(18,2), nullable=False, server_default="0"), sa.Column("extra_kg_fee", sa.Numeric(18,2), nullable=False, server_default="0"),
        sa.Column("return_fee", sa.Numeric(18,2), nullable=False, server_default="0"), sa.Column("insurance_percent", sa.Numeric(7,4), nullable=False, server_default="0"), sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()))

    op.create_table("shipments",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider_id", sa.Integer(), sa.ForeignKey("shipping_providers.id", ondelete="RESTRICT"), nullable=False), sa.Column("service_id", sa.Integer(), sa.ForeignKey("shipping_provider_services.id", ondelete="SET NULL")),
        sa.Column("reference", sa.String(100), nullable=False), sa.Column("external_id", sa.String(150)), sa.Column("tracking_number", sa.String(150)), sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("payment_method", sa.String(30), nullable=False, server_default="prepaid"), sa.Column("cod_amount", sa.Numeric(18,2), nullable=False, server_default="0"),
        sa.Column("shipping_fee", sa.Numeric(18,2), nullable=False, server_default="0"), sa.Column("cod_fee", sa.Numeric(18,2), nullable=False, server_default="0"), sa.Column("other_fee", sa.Numeric(18,2), nullable=False, server_default="0"),
        sa.Column("weight_kg", sa.Numeric(12,3)), sa.Column("volumetric_weight_kg", sa.Numeric(12,3)), sa.Column("customer_name", sa.String(200), nullable=False), sa.Column("customer_phone", sa.String(50)),
        sa.Column("address", sa.Text()), sa.Column("city", sa.String(100)), sa.Column("country_code", sa.String(2), nullable=False, server_default="EG"),
        sa.Column("shipped_at", sa.DateTime(timezone=True)), sa.Column("delivered_at", sa.DateTime(timezone=True)), sa.Column("returned_at", sa.DateTime(timezone=True)), sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    for name, table, cols in [("ix_shipments_tenant_id","shipments",["tenant_id"]),("ix_shipments_provider_id","shipments",["provider_id"]),("ix_shipments_reference","shipments",["reference"]),("ix_shipments_tracking_number","shipments",["tracking_number"]),("ix_shipments_status","shipments",["status"]),("ix_shipments_external_id","shipments",["external_id"])]: op.create_index(name, table, cols)

    op.create_table("shipment_events",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("shipment_id", sa.Integer(), sa.ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(30), nullable=False), sa.Column("event_code", sa.String(80)), sa.Column("description", sa.Text()), sa.Column("event_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("raw_payload", sa.Text()))
    op.create_index("ix_shipment_events_shipment_id", "shipment_events", ["shipment_id"])

    op.create_table("shipping_settlements",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider_id", sa.Integer(), sa.ForeignKey("shipping_providers.id", ondelete="RESTRICT"), nullable=False), sa.Column("settlement_reference", sa.String(150), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True)), sa.Column("period_end", sa.DateTime(timezone=True)), sa.Column("gross_cod", sa.Numeric(18,2), nullable=False, server_default="0"),
        sa.Column("shipping_fees", sa.Numeric(18,2), nullable=False, server_default="0"), sa.Column("cod_fees", sa.Numeric(18,2), nullable=False, server_default="0"), sa.Column("adjustments", sa.Numeric(18,2), nullable=False, server_default="0"),
        sa.Column("net_amount", sa.Numeric(18,2), nullable=False, server_default="0"), sa.Column("status", sa.String(30), nullable=False, server_default="draft"), sa.Column("paid_at", sa.DateTime(timezone=True)), sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.UniqueConstraint("tenant_id", "settlement_reference", name="uq_shipping_settlement_reference"))
    op.create_index("ix_shipping_settlements_tenant_id", "shipping_settlements", ["tenant_id"])
    op.create_index("ix_shipping_settlements_provider_id", "shipping_settlements", ["provider_id"])
    op.create_index("ix_shipping_settlements_status", "shipping_settlements", ["status"])


def downgrade():
    op.drop_table("shipping_settlements")
    op.drop_index("ix_shipment_events_shipment_id", table_name="shipment_events")
    op.drop_table("shipment_events")
    for name in ["ix_shipments_external_id","ix_shipments_status","ix_shipments_tracking_number","ix_shipments_reference","ix_shipments_provider_id","ix_shipments_tenant_id"]: op.drop_index(name, table_name="shipments")
    op.drop_table("shipments")
    op.drop_table("shipping_rate_cards")
    op.drop_table("shipping_payment_profiles")
    op.drop_table("shipping_provider_services")
    op.drop_index("ix_shipping_providers_active", table_name="shipping_providers")
    op.drop_index("ix_shipping_providers_tenant_id", table_name="shipping_providers")
    op.drop_table("shipping_providers")
