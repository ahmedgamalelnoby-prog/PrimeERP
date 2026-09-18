"""allow tenant-configured shipping status codes

Revision ID: 20260919_shipping_status_custom_codes
Revises: 20260918_shipping_cost_timestamp
"""
from alembic import op

revision = "20260919_shipping_status_custom_codes"
down_revision = "20260918_shipping_cost_timestamp"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The authoritative status catalog is shipping_order_statuses. Keeping a
    # database CHECK list here would make tenant-created/custom statuses
    # impossible to use on shipments.
    op.drop_constraint("ck_shipment_status", "shipments", type_="check")


def downgrade() -> None:
    op.create_check_constraint(
        "ck_shipment_status",
        "shipments",
        "status IN ('pending','preparing','packing','picked_up','shipped','in_transit','out_for_delivery','delivering','returning','delivered','returned','cancelled')",
    )
