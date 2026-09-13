"""Add ERP execution state to normalized Salla orders.

Revision ID: 20260913_salla_erp_status
Revises: 20260913_salla_normalized_data
"""

from alembic import op
import sqlalchemy as sa

revision = "20260913_salla_erp_status"
down_revision = "20260913_salla_normalized_data"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "salla_orders",
        sa.Column("erp_status", sa.String(30), nullable=False, server_default="pending"),
    )
    op.add_column("salla_orders", sa.Column("erp_entity_id", sa.Integer(), nullable=True))
    op.add_column("salla_orders", sa.Column("erp_error", sa.Text(), nullable=True))
    op.add_column(
        "salla_orders",
        sa.Column("erp_synced_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_salla_orders_erp_status", "salla_orders", ["erp_status"], unique=False)
    op.create_index("ix_salla_orders_erp_entity_id", "salla_orders", ["erp_entity_id"], unique=False)


def downgrade():
    op.drop_index("ix_salla_orders_erp_entity_id", table_name="salla_orders")
    op.drop_index("ix_salla_orders_erp_status", table_name="salla_orders")
    op.drop_column("salla_orders", "erp_synced_at")
    op.drop_column("salla_orders", "erp_error")
    op.drop_column("salla_orders", "erp_entity_id")
    op.drop_column("salla_orders", "erp_status")
