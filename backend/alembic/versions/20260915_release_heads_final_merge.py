"""Final merge for all migrations added after the previous release-head merge.

The branch accumulated four independent heads after the earlier
20260915_merge_all_heads migration. Keeping a single deterministic Alembic
head is required for reproducible fresh installs and upgrades.
"""

revision = "20260915_release_heads_final_merge"
down_revision = (
    "20260915_saas_lifecycle_integrity",
    "20260915_jurisdiction_effective_date_guards",
    "20260915_merge_reporting_heads",
    "20260915_tax_return_drafts",
)
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
