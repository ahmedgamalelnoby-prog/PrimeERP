"""Merge AR and AP completion heads into one finance graph head."""
revision = "20260920_merge_ar_ap_completion_heads"
down_revision = ("20260920_ar_full_completion", "20260920_ap_completion")
branch_labels = None
depends_on = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
