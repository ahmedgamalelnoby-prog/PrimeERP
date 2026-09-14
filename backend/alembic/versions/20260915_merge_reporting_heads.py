"""merge report delivery migration heads

Revision ID: 20260915_merge_reporting_heads
Revises: 20260915_report_attempt_locking, 20260915_reporting_delivery
"""
revision = "20260915_merge_reporting_heads"
down_revision = ("20260915_report_attempt_locking", "20260915_reporting_delivery")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
