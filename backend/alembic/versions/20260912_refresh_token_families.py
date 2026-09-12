"""add refresh token family tracking

Revision ID: 20260912_refresh_token_families
Revises: 20260912_uom_rbac
"""

from alembic import op
import sqlalchemy as sa

revision = "20260912_refresh_token_families"
down_revision = "20260912_uom_rbac"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("refresh_tokens", sa.Column("family_id", sa.String(length=64), nullable=True))
    op.execute(sa.text("UPDATE refresh_tokens SET family_id = CONCAT('legacy-', id) WHERE family_id IS NULL"))
    op.alter_column("refresh_tokens", "family_id", existing_type=sa.String(length=64), nullable=False)
    op.create_index("ix_refresh_tokens_family_id", "refresh_tokens", ["family_id"], unique=False)


def downgrade():
    op.drop_index("ix_refresh_tokens_family_id", table_name="refresh_tokens")
    op.drop_column("refresh_tokens", "family_id")
