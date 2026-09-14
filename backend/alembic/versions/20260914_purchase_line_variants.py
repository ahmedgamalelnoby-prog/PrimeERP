"""Add variant dimension to purchase lines.

Revision ID: 20260914_purchase_line_variants
Revises: 20260914_variant_inventory_dimension
"""
from alembic import op
import sqlalchemy as sa

revision = "20260914_purchase_line_variants"
down_revision = "20260914_variant_inventory_dimension"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("purchase_lines", sa.Column("variant_id", sa.Integer(), nullable=True))
    op.create_index("ix_purchase_lines_variant_id", "purchase_lines", ["variant_id"])
    op.create_foreign_key("fk_purchase_lines_variant_id", "purchase_lines", "product_variants", ["variant_id"], ["id"], ondelete="RESTRICT")


def downgrade():
    op.drop_constraint("fk_purchase_lines_variant_id", "purchase_lines", type_="foreignkey")
    op.drop_index("ix_purchase_lines_variant_id", table_name="purchase_lines")
    op.drop_column("purchase_lines", "variant_id")
