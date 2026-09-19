"""Merge concurrent global-gap migration heads.

Revision ID: 20260919_merge_global_gap_heads
Revises: 20260919_recipe_variant_identity, 20260919_split_payment_allocations
"""
revision = "20260919_merge_global_gap_heads"
down_revision = ("20260919_recipe_variant_identity", "20260919_split_payment_allocations")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
