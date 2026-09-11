"""add sales order header

Revision ID: 20260911salesorders
Revises: 20260911customers
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "20260911salesorders"
down_revision: Union[str, Sequence[str], None] = "20260911customers"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sales_orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), nullable=False),
        sa.Column("order_number", sa.String(50), nullable=False),
        sa.Column("order_date", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("total_amount", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("reference", sa.String(100)),
        sa.Column("notes", sa.Text()),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["customer_id"], ["sales_customers.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["inventory_warehouses.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("company_id", "order_number", name="uq_sales_order_company_number"),
        sa.CheckConstraint("status IN ('draft','confirmed','partially_shipped','shipped','cancelled')", name="ck_sales_order_status"),
        sa.CheckConstraint("total_amount >= 0", name="ck_sales_order_total"),
    )
    for name, column in (
        ("ix_sales_orders_company_id", "company_id"),
        ("ix_sales_orders_customer_id", "customer_id"),
        ("ix_sales_orders_warehouse_id", "warehouse_id"),
        ("ix_sales_orders_status", "status"),
    ):
        op.create_index(name, "sales_orders", [column])


def downgrade() -> None:
    for name in ("ix_sales_orders_status", "ix_sales_orders_warehouse_id", "ix_sales_orders_customer_id", "ix_sales_orders_company_id"):
        op.drop_index(name, table_name="sales_orders")
    op.drop_table("sales_orders")
