"""Final merge for the post-release migration tails.

The SaaS lifecycle tail and the report-attempt tail are the only independent
heads at this point. The report-attempt tail already contains the reporting,
tax-return, and jurisdiction revisions; those ancestors must not be listed
again as merge parents.
"""

revision = "20260915_release_heads_final_merge"
down_revision = (
    "20260915_saas_lifecycle_integrity",
    "20260915_report_attempt_locking",
)
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
