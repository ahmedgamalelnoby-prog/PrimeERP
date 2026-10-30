"""Backfill legacy global roles into company membership scope."""
from alembic import op
import sqlalchemy as sa


revision = "20261111_backfill_company_membership_roles"
down_revision = "20261110_membership_scoped_roles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("""
        UPDATE company_user_memberships AS membership
        SET role_id = users.role_id
        FROM users
        WHERE users.id = membership.user_id
          AND membership.role_id IS NULL
          AND users.role_id IS NOT NULL
    """))


def downgrade() -> None:
    # Keep assigned roles intact; reversing this data backfill could erase
    # intentional company-specific role assignments made after deployment.
    pass
