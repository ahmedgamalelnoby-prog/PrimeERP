"""add shipping settlement and reconciliation tables

Revision ID: 20260911_shipping_settlement
Revises: 20260911_inventory_rbac
"""
from alembic import op
import sqlalchemy as sa

revision = "20260911_shipping_settlement"
down_revision = "20260911_inventory_rbac"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "shipping_settlement_batches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("carrier_id", sa.Integer(), sa.ForeignKey("shipping_carriers.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("reference", sa.String(100), nullable=False),
        sa.Column("settlement_date", sa.Date(), nullable=False),
        sa.Column("gross_amount", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("carrier_fees", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("net_amount", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("status", sa.String(20), server_default="open", nullable=False),
        sa.Column("notes", sa.Text()),
        sa.UniqueConstraint("company_id", "reference", name="uq_shipping_settlement_batch_reference"),
        sa.CheckConstraint("gross_amount >= 0", name="ck_shipping_settlement_gross"),
        sa.CheckConstraint("carrier_fees >= 0", name="ck_shipping_settlement_fees"),
        sa.CheckConstraint("net_amount >= 0", name="ck_shipping_settlement_net"),
        sa.CheckConstraint("status IN ('open','reconciled','cancelled')", name="ck_shipping_settlement_status"),
    )
    op.create_index("ix_shipping_settlement_batches_company_id", "shipping_settlement_batches", ["company_id"])
    op.create_index("ix_shipping_settlement_batches_carrier_id", "shipping_settlement_batches", ["carrier_id"])

    op.create_table(
        "shipping_shipment_settlements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("batch_id", sa.Integer(), sa.ForeignKey("shipping_settlement_batches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("shipment_id", sa.Integer(), sa.ForeignKey("shipments.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("expected_amount", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("collected_amount", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("carrier_fee", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("net_amount", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("variance", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("reconciled", sa.Boolean(), server_default="false", nullable=False),
        sa.UniqueConstraint("shipment_id", name="uq_shipping_shipment_settlement_shipment"),
        sa.CheckConstraint("expected_amount >= 0", name="ck_shipping_ship_settle_expected"),
        sa.CheckConstraint("collected_amount >= 0", name="ck_shipping_ship_settle_collected"),
        sa.CheckConstraint("carrier_fee >= 0", name="ck_shipping_ship_settle_fee"),
    )
    op.create_index("ix_shipping_shipment_settlements_batch_id", "shipping_shipment_settlements", ["batch_id"])
    op.create_index("ix_shipping_shipment_settlements_shipment_id", "shipping_shipment_settlements", ["shipment_id"], unique=True)


def downgrade():
    op.drop_index("ix_shipping_shipment_settlements_shipment_id", table_name="shipping_shipment_settlements")
    op.drop_index("ix_shipping_shipment_settlements_batch_id", table_name="shipping_shipment_settlements")
    op.drop_table("shipping_shipment_settlements")
    op.drop_index("ix_shipping_settlement_batches_carrier_id", table_name="shipping_settlement_batches")
    op.drop_index("ix_shipping_settlement_batches_company_id", table_name="shipping_settlement_batches")
    op.drop_table("shipping_settlement_batches")
