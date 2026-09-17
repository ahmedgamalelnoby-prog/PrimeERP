"""Finalize the treasury migration lineage.

The product-completion merge is already an ancestor of the production-heads
merge. Declaring both revisions as parents would therefore mix an ancestor
with its descendant and create an invalid Alembic merge graph.
"""
from alembic import op  # noqa: F401

revision = "20260911_treasury_heads_merge"
down_revision = "20260911_production_heads_merge"
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
