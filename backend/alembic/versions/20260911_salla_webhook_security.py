"""add Salla webhook secret environment reference

Revision ID: 20260911_salla_webhook_security
Revises: 20260911_fifo_layer_fix
"""
from alembic import op
import sqlalchemy as sa

revision = "20260911_salla_webhook_security"
down_revision = "20260911_fifo_layer_fix"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "integration_connections",
        sa.Column("webhook_secret_env", sa.String(200), nullable=True),
    )


def downgrade():
    op.drop_column("integration_connections", "webhook_secret_env")
