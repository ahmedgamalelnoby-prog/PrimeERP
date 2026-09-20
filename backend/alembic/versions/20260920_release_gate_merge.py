"""Finalize the completion-wave Alembic chain for release readiness."""
from alembic import op

revision = "20260920_release_gate_merge"
down_revision = "20260920_payroll_journal_link"
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
