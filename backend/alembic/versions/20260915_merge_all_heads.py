"""Merge all currently independent migration heads into one release lineage.

This migration is intentionally empty.  The five heads present on the
release branch were valid independent feature branches, but a production
release must have a single Alembic head so fresh databases and upgrades have
one deterministic migration target.
"""

revision = "20260915_merge_all_heads"
down_revision = (
    "20260914_product_category_fk",
    "20260914_product_variants_uom",
    "20260914_purchase_ppv",
    "20260914_sales_returns",
    "20260915_report_scheduler_leases",
)
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
