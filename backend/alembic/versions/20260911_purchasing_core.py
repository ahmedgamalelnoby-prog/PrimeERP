"""add purchasing suppliers and purchase orders

Revision ID: 20260911purchasing
Revises: 20260911reservations
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "20260911purchasing"
down_revision: Union[str, Sequence[str], None] = "20260911reservations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "purchasing_suppliers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("tax_id", sa.String(100)),
        sa.Column("email", sa.String(200)),
        sa.Column("phone", sa.String(50)),
        sa.Column("address", sa.Text()),
        sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("company_id", "code", name="uq_supplier_company_code"),
        sa.CheckConstraint("is_active IN (0,1)", name="ck_supplier_active"),
    )
    op.create_index("ix_purchasing_suppliers_company_id", "purchasing_suppliers", ["company_id"])

    op.create_table(
        "purchase_orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), nullable=False),
        sa.Column("order_number", sa.String(50), nullable=False),
        sa.Column("order_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("reference", sa.String(100)),
        sa.Column("notes", sa.Text()),
        sa.Column("total_amount", sa.Numeric(18,4), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["supplier_id"], ["purchasing_suppliers.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["inventory_warehouses.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("company_id", "order_number", name="uq_purchase_order_company_number"),
        sa.CheckConstraint("status IN ('draft','approved','partially_received','received','cancelled')", name="ck_purchase_order_status"),
        sa.CheckConstraint("total_amount >= 0", name="ck_purchase_order_total"),
    )
    op.create_index("ix_purchase_orders_company_id", "purchase_orders", ["company_id"])
    op.create_index("ix_purchase_orders_supplier_id", "purchase_orders", ["supplier_id"])
    op.create_index("ix_purchase_orders_warehouse_id", "purchase_orders", ["warehouse_id"])
    op.create_index("ix_purchase_orders_status", "purchase_orders", ["status"])

    op.create_table(
        "purchase_order_lines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("purchase_order_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Numeric(18,4), nullable=False),
        sa.Column("unit_price", sa.Numeric(18,4), nullable=False, server_default="0"),
        sa.Column("received_quantity", sa.Numeric(18,4), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["item_id"], ["inventory_items.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("quantity > 0", name="ck_purchase_line_quantity"),
        sa.CheckConstraint("unit_price >= 0", name="ck_purchase_line_unit_price"),
        sa.CheckConstraint("received_quantity >= 0 AND received_quantity <= quantity", name="ck_purchase_line_received"),
    )
    op.create_index("ix_purchase_order_lines_purchase_order_id", "purchase_order_lines", ["purchase_order_id"])
    op.create_index("ix_purchase_order_lines_item_id", "purchase_order_lines", ["item_id"])


def downgrade() -> None:
    op.drop_index("ix_purchase_order_lines_item_id", table_name="purchase_order_lines")
    op.drop_index("ix_purchase_order_lines_purchase_order_id", table_name="purchase_order_lines")
    op.drop_table("purchase_order_lines")
    for name in ("ix_purchase_orders_status", "ix_purchase_orders_warehouse_id", "ix_purchase_orders_supplier_id", "ix_purchase_orders_company_id"):
        op.drop_index(name, table_name="purchase_orders")
    op.drop_table("purchase_orders")
    op.drop_index("ix_purchasing_suppliers_company_id", table_name="purchasing_suppliers")
    op.drop_table("purchasing_suppliers")
