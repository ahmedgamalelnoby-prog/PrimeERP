"""legacy no-op: location stock is owned by the stock-moves migration

Revision ID: 20260911locstock
Revises: 20260911stockmoves

The original stock-moves migration already creates ``inventory_location_stocks``.
This follow-up migration was accidentally duplicating that DDL on fresh databases.
Keep the revision in the graph for history compatibility, but make it structural
no-op; the stock-moves migration remains the single owner of the table.
"""

from alembic import op

revision = "20260911locstock"
down_revision = "20260911stockmoves"
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
