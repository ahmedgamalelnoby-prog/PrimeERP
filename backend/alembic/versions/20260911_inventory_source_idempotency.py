"""enforce company-scoped inventory source idempotency

Revision ID: 20260911_inventory_source_idempotency
Revises: 20260911_product_final_merge
"""

from alembic import op
import sqlalchemy as sa

revision = "20260911_inventory_source_idempotency"
down_revision = "20260911_product_final_merge"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "uq_inventory_stock_move_source",
        "inventory_stock_moves",
        ["company_id", "source_module", "source_entity", "source_id"],
        unique=True,
        postgresql_where=sa.text(
            "source_module IS NOT NULL AND source_entity IS NOT NULL AND source_id IS NOT NULL"
        ),
    )


def downgrade():
    op.drop_index("uq_inventory_stock_move_source", table_name="inventory_stock_moves")
