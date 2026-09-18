"""Bind Salla public-app installations to the authorizing Salla user.

Revision ID: 20260919_salla_public_app_user_identity
Revises: 20260919_salla_public_app
"""

from alembic import op
import sqlalchemy as sa

revision = "20260919_salla_public_app_user_identity"
down_revision = "20260919_salla_public_app"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("salla_app_installations", sa.Column("salla_user_id", sa.String(160), nullable=True))
    op.create_index("ix_salla_app_installations_salla_user_id", "salla_app_installations", ["salla_user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_salla_app_installations_salla_user_id", table_name="salla_app_installations")
    op.drop_column("salla_app_installations", "salla_user_id")
