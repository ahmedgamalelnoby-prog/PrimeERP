"""merge PrimeERP product completion migration heads

Revision ID: 20260911_product_merge
Revises: 20260911_commerce_accounting, 20260911_commerce_controls, 20260911shipping, 20260911integrations
"""

from alembic import op

revision = "20260911_product_merge"
down_revision = (
    "20260911_commerce_accounting",
    "20260911_commerce_controls",
    "20260911shipping",
    "20260911integrations",
)
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
