"""Shipping foundation."""
from alembic import op
import sqlalchemy as sa
revision="20260921_shipping_foundation"
down_revision="20260921_treasury_foundation"
branch_labels=None
depends_on=None
def upgrade():
    op.create_table("shipping_carriers",
        sa.Column("id",sa.Integer(),primary_key=True),
        sa.Column("tenant_id",sa.Integer(),sa.ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False),
        sa.Column("code",sa.String(50),nullable=False),sa.Column("name",sa.String(150),nullable=False),
        sa.Column("is_active",sa.Boolean(),nullable=False,server_default="true"),
        sa.UniqueConstraint("tenant_id","code",name="uq_shipping_carrier_tenant_code"))
    op.create_table("shipping_carrier_rules",
        sa.Column("id",sa.Integer(),primary_key=True),sa.Column("tenant_id",sa.Integer(),sa.ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False),
        sa.Column("carrier_id",sa.Integer(),sa.ForeignKey("shipping_carriers.id",ondelete="CASCADE"),nullable=False),
        sa.Column("rule_type",sa.String(30),nullable=False),sa.Column("fixed_amount",sa.Numeric(18,2),server_default="0"),
        sa.Column("rate_percent",sa.Numeric(9,4),server_default="0"),sa.Column("amount_per_kg",sa.Numeric(18,4),server_default="0"),
        sa.Column("amount_per_item",sa.Numeric(18,4),server_default="0"),sa.Column("zone",sa.String(80)),
        sa.Column("cod_fee",sa.Numeric(18,2),server_default="0"),sa.Column("visa_withdrawal_fee",sa.Numeric(18,2),server_default="0"),
        sa.Column("priority",sa.Integer(),nullable=False,server_default="100"),sa.Column("is_active",sa.Boolean(),nullable=False,server_default="true"))
    op.create_table("shipments",
        sa.Column("id",sa.Integer(),primary_key=True),sa.Column("tenant_id",sa.Integer(),sa.ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False),
        sa.Column("company_id",sa.Integer(),sa.ForeignKey("companies.id",ondelete="RESTRICT"),nullable=False),sa.Column("branch_id",sa.Integer(),sa.ForeignKey("branches.id",ondelete="RESTRICT"),nullable=False),
        sa.Column("sales_order_id",sa.Integer(),sa.ForeignKey("sales_orders.id",ondelete="SET NULL")),sa.Column("carrier_id",sa.Integer(),sa.ForeignKey("shipping_carriers.id",ondelete="RESTRICT")),
        sa.Column("shipment_number",sa.String(80),nullable=False),sa.Column("tracking_number",sa.String(150)),sa.Column("status",sa.String(30),nullable=False,server_default="preparing"),
        sa.Column("payment_method",sa.String(30)),sa.Column("cod_amount",sa.Numeric(18,2),nullable=False,server_default="0"),
        sa.Column("shipping_charge",sa.Numeric(18,2),nullable=False,server_default="0"),sa.Column("carrier_charge",sa.Numeric(18,2),nullable=False,server_default="0"),
        sa.Column("customer_amount",sa.Numeric(18,2),nullable=False,server_default="0"),sa.Column("dispatched_at",sa.DateTime(timezone=True)),
        sa.Column("delivered_at",sa.DateTime(timezone=True)),sa.Column("returned_at",sa.DateTime(timezone=True)),sa.Column("notes",sa.Text()),
        sa.Column("created_by",sa.Integer(),sa.ForeignKey("users.id",ondelete="SET NULL")),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
        sa.UniqueConstraint("tenant_id","shipment_number",name="uq_shipment_tenant_number"))
    op.create_table("shipment_items",
        sa.Column("id",sa.Integer(),primary_key=True),sa.Column("tenant_id",sa.Integer(),sa.ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False),
        sa.Column("shipment_id",sa.Integer(),sa.ForeignKey("shipments.id",ondelete="CASCADE"),nullable=False),sa.Column("product_id",sa.Integer(),sa.ForeignKey("products.id",ondelete="RESTRICT"),nullable=False),
        sa.Column("quantity",sa.Numeric(18,6),nullable=False))
    op.create_table("shipping_returns",
        sa.Column("id",sa.Integer(),primary_key=True),sa.Column("tenant_id",sa.Integer(),sa.ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False),
        sa.Column("shipment_id",sa.Integer(),sa.ForeignKey("shipments.id",ondelete="RESTRICT"),nullable=False),sa.Column("reason",sa.Text()),
        sa.Column("status",sa.String(30),nullable=False,server_default="requested"),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False))
    op.create_table("carrier_settlements",
        sa.Column("id",sa.Integer(),primary_key=True),sa.Column("tenant_id",sa.Integer(),sa.ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False),
        sa.Column("carrier_id",sa.Integer(),sa.ForeignKey("shipping_carriers.id",ondelete="RESTRICT"),nullable=False),sa.Column("settlement_number",sa.String(80),nullable=False),
        sa.Column("settlement_date",sa.Date(),nullable=False),sa.Column("orders_amount",sa.Numeric(18,2),nullable=False,server_default="0"),
        sa.Column("carrier_charges",sa.Numeric(18,2),nullable=False,server_default="0"),sa.Column("cod_collected",sa.Numeric(18,2),nullable=False,server_default="0"),
        sa.Column("net_amount",sa.Numeric(18,2),nullable=False,server_default="0"),sa.Column("status",sa.String(20),nullable=False,server_default="draft"),
        sa.UniqueConstraint("tenant_id","settlement_number",name="uq_carrier_settlement_tenant_number"))
    op.create_index("ix_shipments_tenant_status","shipments",["tenant_id","status"])
    op.create_index("ix_shipments_tenant_tracking","shipments",["tenant_id","tracking_number"])
def downgrade():
    for t in ["carrier_settlements","shipping_returns","shipment_items","shipments","shipping_carrier_rules","shipping_carriers"]:
        op.drop_table(t)
