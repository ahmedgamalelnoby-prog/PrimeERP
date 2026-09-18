"""add configurable shipping status financial events

Revision ID: 20260918_shipping_status_finance
Revises: 20260918_shipping_pricing_engine
"""
from alembic import op
import sqlalchemy as sa

revision = "20260918_shipping_status_finance"
down_revision = "20260918_shipping_pricing_engine"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "shipping_order_statuses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("name_ar", sa.String(120)),
        sa.Column("parent_code", sa.String(50)),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("financial_actions", sa.Text(), server_default="[]", nullable=False),
        sa.UniqueConstraint("company_id", "code", name="uq_shipping_order_status_company_code"),
        sa.CheckConstraint("sort_order >= 0", name="ck_shipping_order_status_sort"),
    )
    op.create_index("ix_shipping_order_statuses_company_id", "shipping_order_statuses", ["company_id"])

    op.create_table(
        "shipping_status_histories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("shipment_id", sa.Integer(), sa.ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_status", sa.String(50)),
        sa.Column("to_status", sa.String(50), nullable=False),
        sa.Column("changed_on", sa.Date(), nullable=False),
        sa.Column("note", sa.Text()),
    )
    op.create_index("ix_shipping_status_histories_shipment_id", "shipping_status_histories", ["shipment_id"])

    op.create_table(
        "shipping_financial_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("carrier_id", sa.Integer(), sa.ForeignKey("shipping_carriers.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("shipment_id", sa.Integer(), sa.ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_key", sa.String(80), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("debit_role", sa.String(50), nullable=False),
        sa.Column("credit_role", sa.String(50), nullable=False),
        sa.Column("source_status", sa.String(50), nullable=False),
        sa.Column("is_reversal", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("description", sa.Text()),
        sa.UniqueConstraint("shipment_id", "event_key", name="uq_shipping_fin_event_shipment_key"),
        sa.CheckConstraint("amount >= 0", name="ck_shipping_fin_event_amount"),
    )
    op.create_index("ix_shipping_financial_events_company_id", "shipping_financial_events", ["company_id"])
    op.create_index("ix_shipping_financial_events_carrier_id", "shipping_financial_events", ["carrier_id"])
    op.create_index("ix_shipping_financial_events_shipment_id", "shipping_financial_events", ["shipment_id"])
    op.create_index("ix_shipping_financial_events_event_date", "shipping_financial_events", ["event_date"])


def downgrade():
    op.drop_index("ix_shipping_financial_events_event_date", table_name="shipping_financial_events")
    op.drop_index("ix_shipping_financial_events_shipment_id", table_name="shipping_financial_events")
    op.drop_index("ix_shipping_financial_events_carrier_id", table_name="shipping_financial_events")
    op.drop_index("ix_shipping_financial_events_company_id", table_name="shipping_financial_events")
    op.drop_table("shipping_financial_events")
    op.drop_index("ix_shipping_status_histories_shipment_id", table_name="shipping_status_histories")
    op.drop_table("shipping_status_histories")
    op.drop_index("ix_shipping_order_statuses_company_id", table_name="shipping_order_statuses")
    op.drop_table("shipping_order_statuses")
