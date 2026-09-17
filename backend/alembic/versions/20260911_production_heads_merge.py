"""Finalize production hardening migration lineage.

The integrations RBAC migration is already a descendant of the journal-source
idempotency guard. Listing both in this merge would therefore mix an ancestor
with its descendant and create an invalid Alembic graph.
"""

revision = "20260911_production_heads_merge"
down_revision = "20260911_integrations_rbac"
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
