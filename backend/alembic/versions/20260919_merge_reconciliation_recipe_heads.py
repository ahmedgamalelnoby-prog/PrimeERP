"""merge bank reconciliation and recipe migration heads

Revision ID: 20260919_merge_reconciliation_recipe_heads
Revises: 20260919_bank_reconciliation_hardening, 20260919_recipe_external_sku
"""
from alembic import op

revision = "20260919_merge_reconciliation_recipe_heads"
down_revision = (
    "20260919_bank_reconciliation_hardening",
    "20260919_recipe_external_sku",
)
branch_labels = None
depends_on = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
