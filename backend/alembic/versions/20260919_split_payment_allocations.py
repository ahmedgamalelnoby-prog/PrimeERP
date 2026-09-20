"""Compatibility marker for the historical split-payment migration.

The actual constraint correction is performed by
20260919_payment_allocation_split_fix. This revision remains as a no-op
compatibility node so existing migration references stay resolvable.
"""
revision = "20260919_split_payment_allocations"
down_revision = "20260919_payment_allocation_split_fix"
branch_labels = None
depends_on = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
