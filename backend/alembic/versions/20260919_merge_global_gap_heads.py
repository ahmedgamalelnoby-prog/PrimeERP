"""Merge concurrent global-gap migration heads.

Revision ID: 20260919_merge_global_gap_heads
Revises: 20260919_recipe_variant_identity, 20260919_stock_move_reservation
"""
revision = "20260919_merge_global_gap_heads"
down_revision = (
    "20260919_recipe_variant_identity",
    "20260919_stock_move_reservation",
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
