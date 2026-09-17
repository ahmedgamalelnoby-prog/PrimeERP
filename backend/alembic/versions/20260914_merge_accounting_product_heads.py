"""Finalize the accounting/product migration lineage.

The product bundle branch is already an ancestor of
20260914_ifrs_cma_accounting_foundation through the integration/product
mapping migrations. Listing both revisions as merge parents therefore creates
an invalid ancestor/descendant merge. This revision continues from the single
latest descendant instead.
"""

revision = "20260914_merge_accounting_product_heads"
down_revision = "20260914_ifrs_cma_accounting_foundation"
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
