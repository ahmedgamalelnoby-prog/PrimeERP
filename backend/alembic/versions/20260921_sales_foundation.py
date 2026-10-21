"""sales order and invoice foundation
Revision ID: 20260921_sales_foundation
Revises: 20260921_inventory_foundation
"""
from alembic import op
import sqlalchemy as sa
revision="20260921_sales_foundation"
down_revision="20260921_inventory_foundation"
branch_labels=None
depends_on=None
def upgrade():
 op.create_table("sales_orders",
  sa.Column("id",sa.Integer(),primary_key=True),sa.Column("tenant_id",sa.Integer(),nullable=False),
  sa.Column("company_id",sa.Integer(),nullable=False),sa.Column("branch_id",sa.Integer(),nullable=False),
  sa.Column("customer_id",sa.Integer(),nullable=False),sa.Column("order_number",sa.String(80),nullable=False),
  sa.Column("order_date",sa.Date(),nullable=False),sa.Column("status",sa.String(20),nullable=False,server_default="draft"),
  sa.Column("currency_code",sa.String(3),nullable=False,server_default="EGP"),
  sa.Column("subtotal",sa.Numeric(18,2),nullable=False,server_default="0"),sa.Column("tax_total",sa.Numeric(18,2),nullable=False,server_default="0"),
  sa.Column("discount_total",sa.Numeric(18,2),nullable=False,server_default="0"),sa.Column("grand_total",sa.Numeric(18,2),nullable=False,server_default="0"),
  sa.Column("notes",sa.Text()),sa.Column("created_by",sa.Integer()),sa.Column("created_at",sa.TIMESTAMP(timezone=True),server_default=sa.text("now()"),nullable=False),sa.Column("updated_at",sa.TIMESTAMP(timezone=True),server_default=sa.text("now()"),nullable=False),
  sa.ForeignKeyConstraint(["tenant_id"],["tenants.id"],ondelete="CASCADE"),sa.ForeignKeyConstraint(["company_id"],["companies.id"],ondelete="CASCADE"),
  sa.ForeignKeyConstraint(["branch_id"],["branches.id"],ondelete="CASCADE"),sa.ForeignKeyConstraint(["customer_id"],["customers.id"],ondelete="RESTRICT"),
  sa.ForeignKeyConstraint(["created_by"],["users.id"],ondelete="SET NULL"),sa.UniqueConstraint("tenant_id","order_number",name="uq_sales_orders_tenant_number"))
 op.create_index("ix_sales_orders_tenant","sales_orders",["tenant_id"]);op.create_index("ix_sales_orders_company","sales_orders",["company_id"]);op.create_index("ix_sales_orders_customer","sales_orders",["customer_id"]);op.create_index("ix_sales_orders_status","sales_orders",["status"])
 op.create_table("sales_order_lines",
  sa.Column("id",sa.Integer(),primary_key=True),sa.Column("order_id",sa.Integer(),nullable=False),sa.Column("product_id",sa.Integer(),nullable=False),
  sa.Column("quantity",sa.Numeric(18,6),nullable=False),sa.Column("unit_price",sa.Numeric(18,2),nullable=False),sa.Column("discount",sa.Numeric(18,2),nullable=False,server_default="0"),
  sa.Column("tax_rate",sa.Numeric(9,4),nullable=False,server_default="0"),sa.Column("line_total",sa.Numeric(18,2),nullable=False),
  sa.ForeignKeyConstraint(["order_id"],["sales_orders.id"],ondelete="CASCADE"),sa.ForeignKeyConstraint(["product_id"],["products.id"],ondelete="RESTRICT"))
 op.create_index("ix_sales_order_lines_order","sales_order_lines",["order_id"])
 op.create_table("sales_invoices",
  sa.Column("id",sa.Integer(),primary_key=True),sa.Column("tenant_id",sa.Integer(),nullable=False),sa.Column("company_id",sa.Integer(),nullable=False),sa.Column("branch_id",sa.Integer(),nullable=False),
  sa.Column("customer_id",sa.Integer(),nullable=False),sa.Column("sales_order_id",sa.Integer()),sa.Column("invoice_number",sa.String(80),nullable=False),
  sa.Column("invoice_date",sa.Date(),nullable=False),sa.Column("status",sa.String(20),nullable=False,server_default="draft"),sa.Column("currency_code",sa.String(3),nullable=False,server_default="EGP"),
  sa.Column("subtotal",sa.Numeric(18,2),nullable=False,server_default="0"),sa.Column("tax_total",sa.Numeric(18,2),nullable=False,server_default="0"),sa.Column("discount_total",sa.Numeric(18,2),nullable=False,server_default="0"),sa.Column("grand_total",sa.Numeric(18,2),nullable=False,server_default="0"),
  sa.Column("created_by",sa.Integer()),sa.Column("created_at",sa.TIMESTAMP(timezone=True),server_default=sa.text("now()"),nullable=False),sa.Column("updated_at",sa.TIMESTAMP(timezone=True),server_default=sa.text("now()"),nullable=False),
  sa.ForeignKeyConstraint(["tenant_id"],["tenants.id"],ondelete="CASCADE"),sa.ForeignKeyConstraint(["company_id"],["companies.id"],ondelete="CASCADE"),sa.ForeignKeyConstraint(["branch_id"],["branches.id"],ondelete="CASCADE"),sa.ForeignKeyConstraint(["customer_id"],["customers.id"],ondelete="RESTRICT"),sa.ForeignKeyConstraint(["sales_order_id"],["sales_orders.id"],ondelete="SET NULL"),sa.ForeignKeyConstraint(["created_by"],["users.id"],ondelete="SET NULL"),sa.UniqueConstraint("tenant_id","invoice_number",name="uq_sales_invoices_tenant_number"))
 op.create_index("ix_sales_invoices_tenant","sales_invoices",["tenant_id"]);op.create_index("ix_sales_invoices_customer","sales_invoices",["customer_id"]);op.create_index("ix_sales_invoices_status","sales_invoices",["status"])
def downgrade():
 op.drop_table("sales_invoices");op.drop_table("sales_order_lines");op.drop_table("sales_orders")
