"""Finalize the post-release migration lineage.

All report, tax-return, and jurisdiction revisions are already ancestors of
20260915_saas_lifecycle_integrity through the earlier release merge chain.
This revision therefore extends the single remaining SaaS tail instead of
listing an ancestor as a second merge parent.
"""

revision = "20260915_release_heads_final_merge"
down_revision = "20260915_saas_lifecycle_integrity"
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
