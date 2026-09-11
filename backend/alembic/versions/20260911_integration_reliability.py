"""add integration webhook reliability fields

Revision ID: 20260911_integration_reliability
Revises: 20260911_shipping_journal
"""
from alembic import op
import sqlalchemy as sa

revision = "20260911_integration_reliability"
down_revision = "20260911_shipping_journal"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("integration_events", sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("integration_events", sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("integration_events", sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("integration_events", sa.Column("last_error", sa.Text(), nullable=True))
    op.create_index("ix_integration_events_retry", "integration_events", ["status", "next_attempt_at"])


def downgrade():
    op.drop_index("ix_integration_events_retry", table_name="integration_events")
    op.drop_column("integration_events", "last_error")
    op.drop_column("integration_events", "processed_at")
    op.drop_column("integration_events", "next_attempt_at")
    op.drop_column("integration_events", "attempts")
