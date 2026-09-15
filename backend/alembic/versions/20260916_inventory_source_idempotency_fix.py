"""Fix inventory source idempotency so manual moves may have NULL source metadata.

Revision ID: 20260916_inventory_source_idempotency_fix
Revises: 20260916_release_graph_inventory_commissions_merge
"""

from alembic import op
import sqlalchemy as sa

revision = "20260916_inventory_source_idempotency_fix"
down_revision = "20260916_release_graph_inventory_commissions_merge"
branch_labels = None
depends_on = None


INDEX_NAME = "uq_inventory_stock_move_source_nonnull"
LEGACY_CONSTRAINT = "uq_inventory_stock_move_source"


def upgrade():
    bind = op.get_bind()

    # The previous constraint used PostgreSQL NULLS NOT DISTINCT, which made
    # unrelated manual movements with NULL source fields collide. Replace it
    # with a partial unique index that applies only to fully specified source
    # references.
    inspector = sa.inspect(bind)
    unique_constraints = {
        item["name"]
        for item in inspector.get_unique_constraints("inventory_stock_moves")
        if item.get("name")
    }
    if LEGACY_CONSTRAINT in unique_constraints:
        op.drop_constraint(LEGACY_CONSTRAINT, "inventory_stock_moves", type_="unique")

    indexes = {
        item["name"]
        for item in inspector.get_indexes("inventory_stock_moves")
        if item.get("name")
    }
    if INDEX_NAME not in indexes:
        op.create_index(
            INDEX_NAME,
            "inventory_stock_moves",
            ["company_id", "source_module", "source_entity", "source_id"],
            unique=True,
            postgresql_where=sa.text(
                "source_module IS NOT NULL AND source_entity IS NOT NULL AND source_id IS NOT NULL"
            ),
        )


def downgrade():
    bind = op.get_bind()
    indexes = {
        item["name"]
        for item in sa.inspect(bind).get_indexes("inventory_stock_moves")
        if item.get("name")
    }
    if INDEX_NAME in indexes:
        op.drop_index(INDEX_NAME, table_name="inventory_stock_moves")

    # Restore the legacy semantics on downgrade for compatibility with the
    # immediately preceding migration.
    op.create_unique_constraint(
        LEGACY_CONSTRAINT,
        "inventory_stock_moves",
        ["company_id", "source_module", "source_entity", "source_id"],
        postgresql_nulls_not_distinct=True,
    )
