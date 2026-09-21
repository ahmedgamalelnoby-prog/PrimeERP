"""add POS domain core

Revision ID: 20260921_pos_domain
Revises: 20260921_purchasing_treasury_rbac
"""
from alembic import op
import sqlalchemy as sa

revision="20260921_pos_domain"
down_revision="20260921_purchasing_treasury_rbac"
branch_labels=None
depends_on=None

def upgrade():
    op.create_table("pos_outlets",
        sa.Column("id",sa.Integer(),primary_key=True),
        sa.Column("company_id",sa.Integer(),sa.ForeignKey("companies.id",ondelete="CASCADE"),nullable=False),
        sa.Column("branch_id",sa.Integer(),sa.ForeignKey("branches.id",ondelete="RESTRICT"),nullable=False),
        sa.Column("inventory_location_id",sa.Integer(),sa.ForeignKey("inventory_locations.id",ondelete="RESTRICT"),nullable=False),
        sa.Column("code",sa.String(60),nullable=False),sa.Column("name",sa.String(200),nullable=False),sa.Column("is_active",sa.Boolean(),nullable=False,server_default=sa.true()),
        sa.UniqueConstraint("company_id","code",name="uq_pos_outlet_company_code"))
    op.create_index("ix_pos_outlets_company_id","pos_outlets",["company_id"])
    op.create_table("pos_devices",
        sa.Column("id",sa.Integer(),primary_key=True),sa.Column("company_id",sa.Integer(),sa.ForeignKey("companies.id",ondelete="CASCADE"),nullable=False),
        sa.Column("outlet_id",sa.Integer(),sa.ForeignKey("pos_outlets.id",ondelete="CASCADE"),nullable=False),
        sa.Column("code",sa.String(60),nullable=False),sa.Column("name",sa.String(160),nullable=False),sa.Column("is_active",sa.Boolean(),nullable=False,server_default=sa.true()),
        sa.UniqueConstraint("company_id","code",name="uq_pos_device_company_code"))
    op.create_index("ix_pos_devices_company_id","pos_devices",["company_id"]);op.create_index("ix_pos_devices_outlet_id","pos_devices",["outlet_id"])
    op.create_table("pos_sessions",
        sa.Column("id",sa.Integer(),primary_key=True),sa.Column("company_id",sa.Integer(),sa.ForeignKey("companies.id",ondelete="CASCADE"),nullable=False),
        sa.Column("outlet_id",sa.Integer(),sa.ForeignKey("pos_outlets.id",ondelete="RESTRICT"),nullable=False),sa.Column("device_id",sa.Integer(),sa.ForeignKey("pos_devices.id",ondelete="RESTRICT"),nullable=False),
        sa.Column("cashier_user_id",sa.Integer(),sa.ForeignKey("users.id",ondelete="RESTRICT"),nullable=False),sa.Column("status",sa.String(20),nullable=False,server_default="open"),
        sa.Column("opened_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),sa.Column("closed_at",sa.DateTime(timezone=True)),sa.Column("closing_total",sa.Numeric(18,4)),
        sa.CheckConstraint("status IN ('open','closed','cancelled')",name="ck_pos_session_status"))
    op.create_index("ix_pos_sessions_company_id","pos_sessions",["company_id"]);op.create_index("ix_pos_sessions_device_id","pos_sessions",["device_id"])
    op.create_table("pos_orders",
        sa.Column("id",sa.Integer(),primary_key=True),sa.Column("company_id",sa.Integer(),sa.ForeignKey("companies.id",ondelete="CASCADE"),nullable=False),
        sa.Column("session_id",sa.Integer(),sa.ForeignKey("pos_sessions.id",ondelete="RESTRICT"),nullable=False),sa.Column("number",sa.String(80),nullable=False),
        sa.Column("status",sa.String(20),nullable=False,server_default="draft"),sa.Column("subtotal",sa.Numeric(18,4),nullable=False,server_default="0"),
        sa.Column("tax_total",sa.Numeric(18,4),nullable=False,server_default="0"),sa.Column("total",sa.Numeric(18,4),nullable=False,server_default="0"),sa.Column("paid_total",sa.Numeric(18,4),nullable=False,server_default="0"),sa.Column("finalized_at",sa.DateTime(timezone=True)),
        sa.UniqueConstraint("company_id","number",name="uq_pos_order_company_number"),sa.CheckConstraint("status IN ('draft','finalized','cancelled','reversed')",name="ck_pos_order_status"))
    op.create_index("ix_pos_orders_company_id","pos_orders",["company_id"]);op.create_index("ix_pos_orders_session_id","pos_orders",["session_id"])
    op.create_table("pos_order_lines",
        sa.Column("id",sa.Integer(),primary_key=True),sa.Column("order_id",sa.Integer(),sa.ForeignKey("pos_orders.id",ondelete="CASCADE"),nullable=False),
        sa.Column("item_id",sa.Integer(),sa.ForeignKey("inventory_items.id",ondelete="RESTRICT"),nullable=False),sa.Column("variant_id",sa.Integer(),sa.ForeignKey("product_variants.id",ondelete="RESTRICT")),
        sa.Column("quantity",sa.Numeric(18,4),nullable=False),sa.Column("unit_price",sa.Numeric(18,4),nullable=False),sa.Column("tax_percent",sa.Numeric(8,4),nullable=False,server_default="0"),
        sa.Column("line_subtotal",sa.Numeric(18,4),nullable=False),sa.Column("line_tax",sa.Numeric(18,4),nullable=False,server_default="0"),sa.Column("line_total",sa.Numeric(18,4),nullable=False),sa.Column("recipe_id",sa.Integer(),sa.ForeignKey("recipes.id",ondelete="SET NULL")))
    op.create_index("ix_pos_order_lines_order_id","pos_order_lines",["order_id"])
    op.create_table("pos_payments",
        sa.Column("id",sa.Integer(),primary_key=True),sa.Column("company_id",sa.Integer(),sa.ForeignKey("companies.id",ondelete="CASCADE"),nullable=False),
        sa.Column("order_id",sa.Integer(),sa.ForeignKey("pos_orders.id",ondelete="RESTRICT"),nullable=False),sa.Column("method",sa.String(20),nullable=False),
        sa.Column("amount",sa.Numeric(18,4),nullable=False),sa.Column("idempotency_key",sa.String(120),nullable=False),sa.Column("status",sa.String(20),nullable=False,server_default="posted"),
        sa.Column("accounting_entry_id",sa.Integer(),sa.ForeignKey("journal_entries.id",ondelete="RESTRICT")),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),
        sa.UniqueConstraint("company_id","idempotency_key",name="uq_pos_payment_idempotency"),sa.CheckConstraint("method IN ('cash','card','bank','other')",name="ck_pos_payment_method"),sa.CheckConstraint("amount > 0",name="ck_pos_payment_amount"),sa.CheckConstraint("status IN ('posted','reversed')",name="ck_pos_payment_status"))
    op.create_index("ix_pos_payments_company_id","pos_payments",["company_id"]);op.create_index("ix_pos_payments_order_id","pos_payments",["order_id"])

def downgrade():
    op.drop_table("pos_payments");op.drop_table("pos_order_lines");op.drop_table("pos_orders");op.drop_table("pos_sessions");op.drop_table("pos_devices");op.drop_table("pos_outlets")
