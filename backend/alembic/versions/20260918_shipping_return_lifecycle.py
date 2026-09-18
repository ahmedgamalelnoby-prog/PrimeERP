"""harden shipping return lifecycle

Revision ID: 20260918_shipping_return_lifecycle
Revises: 20260918_shipping_status_finance
"""
from alembic import op

revision = "20260918_shipping_return_lifecycle"
down_revision = "20260918_shipping_status_finance"
branch_labels = None
depends_on = None


def upgrade():
    # A returned shipment must not transition back to delivered because the
    # delivered financial events are intentionally idempotent per shipment.
    # Re-delivery should be represented by a new shipment/re-dispatch.
    op.execute(
        "UPDATE shipping_order_statuses SET allowed_next_codes='[\\\"returned\\\"]' "        "WHERE code='returning' AND allowed_next_codes='[\\\"returned\\\", \\\"delivered\\\"]'"
    )


def downgrade():
    op.execute(
        "UPDATE shipping_order_statuses SET allowed_next_codes='[\\\"returned\\\", \\\"delivered\\\"]' "        "WHERE code='returning' AND allowed_next_codes='[\\\"returned\\\"]'"
    )
