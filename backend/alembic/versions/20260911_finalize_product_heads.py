"""merge final PrimeERP product-completion migration heads

Revision ID: 20260911_product_final_merge
Revises: 20260911_commerce_wht, 20260911_salla_mappings
"""

from alembic import op

revision = "20260911_product_final_merge"
down_revision = (
    "20260911_commerce_wht",
    "20260911_salla_mappings",
)
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
