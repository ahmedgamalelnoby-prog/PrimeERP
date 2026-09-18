"""Add external subscription identity for marketplace billing.

Revision ID: 20260919_salla_subscription_identity
Revises: 20260919_salla_public_app_user_identity
"""

from alembic import op
import sqlalchemy as sa

revision = "20260919_salla_subscription_identity"
down_revision = "20260919_salla_public_app_user_identity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("subscriptions", sa.Column("external_provider", sa.String(40), nullable=True))
    op.add_column("subscriptions", sa.Column("external_subscription_id", sa.String(160), nullable=True))
    op.create_index("ix_subscriptions_external_provider", "subscriptions", ["external_provider"], unique=False)
    op.create_index("ix_subscriptions_external_subscription_id", "subscriptions", ["external_subscription_id"], unique=False)
    op.create_index(
        "uq_subscriptions_external_identity",
        "subscriptions",
        ["external_provider", "external_subscription_id"],
        unique=True,
        postgresql_where=sa.text("external_provider IS NOT NULL AND external_subscription_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_subscriptions_external_identity", table_name="subscriptions")
    op.drop_index("ix_subscriptions_external_subscription_id", table_name="subscriptions")
    op.drop_index("ix_subscriptions_external_provider", table_name="subscriptions")
    op.drop_column("subscriptions", "external_subscription_id")
    op.drop_column("subscriptions", "external_provider")
