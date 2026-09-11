"""merge the existing production and product-completion migration heads

Revision ID: 20260911_treasury_heads_merge
Revises: 20260911_production_heads_merge, 20260911_product_merge
"""
from alembic import op

revision = "20260911_treasury_heads_merge"
down_revision = ("20260911_production_heads_merge", "20260911_product_merge")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
