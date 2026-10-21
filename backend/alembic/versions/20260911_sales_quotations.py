"""add sales quotations

Revision ID: 20260911salesquotations
Revises: 20260911salesorders
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "20260911salesquotations"
down_revision: Union[str, Sequence[str], None] = "20260911salesorders"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table("sales_quotations",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False), sa.Column("quotation_number", sa.String(50), nullable=False),
        sa.Column("quotation_date", sa.String(20), nullable=False), sa.Column("valid_until", sa.String(20)),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"), sa.Column("total_amount", sa.Numeric(18,4), nullable=False, server_default="0"), sa.Column("notes", sa.Text()),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["customer_id"], ["sales_customers.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("company_id", "quotation_number", name="uq_sales_quotation_company_number"),
        sa.CheckConstraint("status IN ('draft','sent','accepted','rejected','expired','cancelled')", name="ck_sales_quotation_status"), sa.CheckConstraint("total_amount >= 0", name="ck_sales_quotation_total"))
    op.create_index("ix_sales_quotations_company_id", "sales_quotations", ["company_id"])
    op.create_index("ix_sales_quotations_customer_id", "sales_quotations", ["customer_id"])
    op.create_index("ix_sales_quotations_status", "sales_quotations", ["status"])
    op.create_table("sales_quotation_lines",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("quotation_id", sa.Integer(), nullable=False), sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Numeric(18,4), nullable=False), sa.Column("unit_price", sa.Numeric(18,4), nullable=False), sa.Column("discount_amount", sa.Numeric(18,4), nullable=False, server_default="0"), sa.Column("line_total", sa.Numeric(18,4), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["quotation_id"], ["sales_quotations.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["item_id"], ["inventory_items.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("quantity > 0", name="ck_sales_quotation_line_qty"), sa.CheckConstraint("unit_price >= 0", name="ck_sales_quotation_line_price"), sa.CheckConstraint("discount_amount >= 0", name="ck_sales_quotation_line_discount"), sa.CheckConstraint("line_total >= 0", name="ck_sales_quotation_line_total"))
    op.create_index("ix_sales_quotation_lines_quotation_id", "sales_quotation_lines", ["quotation_id"])
    op.create_index("ix_sales_quotation_lines_item_id", "sales_quotation_lines", ["item_id"])


def downgrade() -> None:
    op.drop_index("ix_sales_quotation_lines_item_id", table_name="sales_quotation_lines"); op.drop_index("ix_sales_quotation_lines_quotation_id", table_name="sales_quotation_lines"); op.drop_table("sales_quotation_lines")
    op.drop_index("ix_sales_quotations_status", table_name="sales_quotations"); op.drop_index("ix_sales_quotations_customer_id", table_name="sales_quotations"); op.drop_index("ix_sales_quotations_company_id", table_name="sales_quotations"); op.drop_table("sales_quotations")
