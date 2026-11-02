"""Merge inventory transfer and approval workflow migration heads."""

revision = "20261106_merge_inventory_approval_heads"
down_revision = (
    "20260922_inventory_transfer_quantities",
    "20261105_approval_workflow_tables",
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
