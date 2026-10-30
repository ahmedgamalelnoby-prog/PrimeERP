"""Add company and branch scoped role overrides to membership grants."""
from alembic import op
import sqlalchemy as sa


revision = "20261110_membership_scoped_roles"
down_revision = "20261109_branch_user_memberships"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "company_user_memberships",
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_company_user_memberships_role_id", "company_user_memberships", ["role_id"])
    op.add_column(
        "branch_user_memberships",
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_branch_user_memberships_role_id", "branch_user_memberships", ["role_id"])


def downgrade() -> None:
    op.drop_index("ix_branch_user_memberships_role_id", table_name="branch_user_memberships")
    op.drop_column("branch_user_memberships", "role_id")
    op.drop_index("ix_company_user_memberships_role_id", table_name="company_user_memberships")
    op.drop_column("company_user_memberships", "role_id")
