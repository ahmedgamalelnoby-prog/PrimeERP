"""Harden inventory transaction audit and idempotency.

Revision ID: 20260916_inventory_transaction_integrity
Revises: 20260916_enterprise_module_integrity
"""

from alembic import op
import sqlalchemy as sa

revision = "20260916_inventory_transaction_integrity"
down_revision = "20260916_enterprise_module_integrity"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()

    # Existing data must be clean before adding the source idempotency key.
    duplicate = bind.execute(sa.text("""
        SELECT company_id, source_module, source_entity, source_id
        FROM inventory_stock_moves
        WHERE source_module IS NOT NULL AND source_entity IS NOT NULL AND source_id IS NOT NULL
        GROUP BY company_id, source_module, source_entity, source_id
        HAVING COUNT(*) > 1
        LIMIT 1
    """)).first()
    if duplicate is not None:
        raise RuntimeError("Cannot harden inventory stock moves: duplicate source references exist")

    op.add_column(
        "inventory_stock_moves",
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "inventory_stock_moves",
        sa.Column("accounting_entry_id", sa.Integer(), nullable=True),
    )
    op.create_index("ix_inventory_stock_moves_posted_at", "inventory_stock_moves", ["posted_at"])
    op.create_index("ix_inventory_stock_moves_accounting_entry_id", "inventory_stock_moves", ["accounting_entry_id"])
    op.create_foreign_key(
        "fk_inventory_stock_move_accounting_entry",
        "inventory_stock_moves",
        "journal_entries",
        ["accounting_entry_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_unique_constraint(
        "uq_inventory_stock_move_source",
        "inventory_stock_moves",
        ["company_id", "source_module", "source_entity", "source_id"],
        postgresql_nulls_not_distinct=True,
    )


def downgrade():
    op.drop_constraint("uq_inventory_stock_move_source", "inventory_stock_moves", type_="unique")
    op.drop_constraint("fk_inventory_stock_move_accounting_entry", "inventory_stock_moves", type_="foreignkey")
    op.drop_index("ix_inventory_stock_moves_accounting_entry_id", table_name="inventory_stock_moves")
    op.drop_index("ix_inventory_stock_moves_posted_at", table_name="inventory_stock_moves")
    op.drop_column("inventory_stock_moves", "accounting_entry_id")
    op.drop_column("inventory_stock_moves", "posted_at")
