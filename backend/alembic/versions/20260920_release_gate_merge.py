"""Merge the remaining completion-wave Alembic heads for release readiness."""
from alembic import op

revision = "20260920_release_gate_merge"
down_revision = (
    "20260920_commerce_partial_fulfillment",
    "20260920_domain_completion_wave",
    "20260920_payroll_journal_link",
    "20260920_security_completion_wave2",
)
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
