"""Add explicit user-to-branch access assignments.

Revision ID: 20261107_user_branch_memberships
Revises: 20261106_merge_inventory_approval_heads
"""
from alembic import op
import sqlalchemy as sa

revision = "20261107_user_branch_memberships"
down_revision = "20261106_merge_inventory_approval_heads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_branch_memberships",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.Integer(),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "branch_id",
            sa.Integer(),
            sa.ForeignKey("branches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "assigned_by_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "tenant_id",
            "user_id",
            "branch_id",
            name="uq_user_branch_memberships_tenant_user_branch",
        ),
    )
    op.create_index(
        "ix_user_branch_memberships_tenant_id",
        "user_branch_memberships",
        ["tenant_id"],
    )
    op.create_index(
        "ix_user_branch_memberships_user_id",
        "user_branch_memberships",
        ["user_id"],
    )
    op.create_index(
        "ix_user_branch_memberships_branch_id",
        "user_branch_memberships",
        ["branch_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_user_branch_memberships_branch_id", table_name="user_branch_memberships")
    op.drop_index("ix_user_branch_memberships_user_id", table_name="user_branch_memberships")
    op.drop_index("ix_user_branch_memberships_tenant_id", table_name="user_branch_memberships")
    op.drop_table("user_branch_memberships")
