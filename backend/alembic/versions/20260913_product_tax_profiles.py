"""Add product tax profiles and persist commerce tax stacks.

Revision ID: 20260913_product_tax_profiles
Revises: 20260913_inventory_uom_integration
"""

from alembic import op
import sqlalchemy as sa

revision = "20260913_product_tax_profiles"
down_revision = "20260913_inventory_uom_integration"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("inventory_items", sa.Column("sales_tax_ids", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("inventory_items", sa.Column("purchase_tax_ids", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("sales_lines", sa.Column("tax_rate_ids", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("purchase_lines", sa.Column("tax_rate_ids", sa.JSON(), nullable=False, server_default="[]"))
    op.alter_column("inventory_items", "sales_tax_ids", server_default=None)
    op.alter_column("inventory_items", "purchase_tax_ids", server_default=None)
    op.alter_column("sales_lines", "tax_rate_ids", server_default=None)
    op.alter_column("purchase_lines", "tax_rate_ids", server_default=None)


def downgrade():
    op.drop_column("purchase_lines", "tax_rate_ids")
    op.drop_column("sales_lines", "tax_rate_ids")
    op.drop_column("inventory_items", "purchase_tax_ids")
    op.drop_column("inventory_items", "sales_tax_ids")
