"""add Salla public app event idempotency ledger

Revision ID: 20260919_salla_app_event_idempotency
Revises: 20260919_merge_global_gap_heads
"""

from alembic import op
import sqlalchemy as sa

revision = "20260919_salla_app_event_idempotency"
down_revision = "20260919_merge_global_gap_heads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "salla_app_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("merchant_id", sa.String(length=160), nullable=False),
        sa.Column("event_id", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=160), nullable=False),
        sa.Column("payload_sha256", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="processing"),
        sa.Column("result_json", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("merchant_id", "event_id", name="uq_salla_app_event_merchant_event"),
    )
    op.create_index("ix_salla_app_events_merchant_id", "salla_app_events", ["merchant_id"])
    op.create_index("ix_salla_app_events_status", "salla_app_events", ["status"])


def downgrade() -> None:
    op.drop_index("ix_salla_app_events_status", table_name="salla_app_events")
    op.drop_index("ix_salla_app_events_merchant_id", table_name="salla_app_events")
    op.drop_table("salla_app_events")
