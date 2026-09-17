"""Merge report delivery migration tails.

The report-attempt locking migration already descends from the tax-return draft
and reporting delivery revisions, so those revisions must not be repeated as
second parents here.
"""

revision = "20260915_merge_reporting_heads"
down_revision = "20260915_report_attempt_locking"
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
