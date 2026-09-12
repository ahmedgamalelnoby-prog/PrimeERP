"""merge PrimeERP product completion migration heads

Revision ID: 20260911_product_merge
Revises: 20260911_commerce_accounting, 20260911_commerce_controls, 20260911shipping

The integrations migration is an ancestor of UOM and therefore of both
commerce-control branches. Including it separately here creates an invalid
Alembic merge graph and can trigger KeyError while upgrading a fresh database.
"""

revision = "20260911_product_merge"
down_revision = (
    "20260911_commerce_accounting",
    "20260911_commerce_controls",
    "20260911shipping",
)
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
