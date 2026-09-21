"""Merge the remaining domain-completion Alembic heads."""
from alembic import op

revision = "20260921_merge_domain_completion_heads"
down_revision = (
    "20260920_commerce_partial_fulfillment",
    "20260920_cost_mrp_completion",
    "20260920_domain_completion_wave",
)
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass
