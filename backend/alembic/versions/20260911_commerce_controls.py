"""strengthen commerce lifecycle

Revision ID: 20260911_commerce_controls
Revises: 20260911_uom
"""
from alembic import op
import sqlalchemy as sa

revision = "20260911_commerce_controls"
down_revision = "20260911_uom"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("sales_lines", sa.Column("tax_rate_id", sa.Integer(), nullable=True))
    op.create_index("ix_sales_lines_tax_rate_id", "sales_lines", ["tax_rate_id"])
    op.create_foreign_key("fk_sales_lines_tax_rate_id", "sales_lines", "tax_rates", ["tax_rate_id"], ["id"], ondelete="RESTRICT")

    op.add_column("purchase_lines", sa.Column("tax_rate_id", sa.Integer(), nullable=True))
    op.create_index("ix_purchase_lines_tax_rate_id", "purchase_lines", ["tax_rate_id"])
    op.create_foreign_key("fk_purchase_lines_tax_rate_id", "purchase_lines", "tax_rates", ["tax_rate_id"], ["id"], ondelete="RESTRICT")

    op.add_column("commerce_payments", sa.Column("status", sa.String(20), nullable=False, server_default="posted"))
    op.add_column("commerce_payments", sa.Column("reversed_of_id", sa.Integer(), nullable=True))
    op.add_column("commerce_payments", sa.Column("reversed_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_commerce_payments_reversed_of_id", "commerce_payments", ["reversed_of_id"])
    op.create_foreign_key("fk_commerce_payments_reversed_of_id", "commerce_payments", "commerce_payments", ["reversed_of_id"], ["id"], ondelete="RESTRICT")
    op.create_check_constraint("ck_commerce_payment_status", "commerce_payments", "status IN ('posted','reversed')")


def downgrade():
    op.drop_constraint("ck_commerce_payment_status", "commerce_payments", type_="check")
    op.drop_constraint("fk_commerce_payments_reversed_of_id", "commerce_payments", type_="foreignkey")
    op.drop_index("ix_commerce_payments_reversed_of_id", table_name="commerce_payments")
    op.drop_column("commerce_payments", "reversed_at")
    op.drop_column("commerce_payments", "reversed_of_id")
    op.drop_column("commerce_payments", "status")

    op.drop_constraint("fk_purchase_lines_tax_rate_id", "purchase_lines", type_="foreignkey")
    op.drop_index("ix_purchase_lines_tax_rate_id", table_name="purchase_lines")
    op.drop_column("purchase_lines", "tax_rate_id")

    op.drop_constraint("fk_sales_lines_tax_rate_id", "sales_lines", type_="foreignkey")
    op.drop_index("ix_sales_lines_tax_rate_id", table_name="sales_lines")
    op.drop_column("sales_lines", "tax_rate_id")
