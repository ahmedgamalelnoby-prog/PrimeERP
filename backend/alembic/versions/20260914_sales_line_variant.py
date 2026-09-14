"""add variant reference to sales lines

Revision ID: 20260914_sales_line_variant
Revises: 20260914_fix_integration_product_mapping_local_unique
"""
from alembic import op
import sqlalchemy as sa

revision = "20260914_sales_line_variant"
down_revision = "20260914_fix_integration_product_mapping_local_unique"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "sales_lines",
        sa.Column("variant_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_sales_lines_variant_id",
        "sales_lines",
        "product_variants",
        ["variant_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_sales_lines_variant_id",
        "sales_lines",
        ["variant_id"],
    )


def downgrade():
    op.drop_index("ix_sales_lines_variant_id", table_name="sales_lines")
    op.drop_constraint("fk_sales_lines_variant_id", "sales_lines", type_="foreignkey")
    op.drop_column("sales_lines", "variant_id")
