"""merge production hardening migration heads

Revision ID: 20260911_production_heads_merge
Revises: 20260911_journal_source_guard, 20260911_integrations_rbac
"""

revision = "20260911_production_heads_merge"
down_revision = ("20260911_journal_source_guard", "20260911_integrations_rbac")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
