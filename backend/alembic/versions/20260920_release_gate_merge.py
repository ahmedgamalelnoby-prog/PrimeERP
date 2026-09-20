"""Merge the independent completion-wave Alembic heads into one release head."""
revision = "20260920_release_gate_merge"
down_revision = (
    "20260920_commerce_partial_fulfillment",
    "20260920_domain_completion_wave",
    "20260920_security_completion_wave2",
)
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
