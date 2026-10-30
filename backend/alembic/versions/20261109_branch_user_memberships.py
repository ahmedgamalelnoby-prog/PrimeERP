"""Create explicit user-to-branch access grants."""
from alembic import op
import sqlalchemy as sa


revision = "20261109_branch_user_memberships"
down_revision = "20261108_company_user_memberships"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "branch_user_memberships",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "branch_id",
            sa.Integer(),
            sa.ForeignKey("branches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "assigned_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("branch_id", "user_id", name="uq_branch_user_membership"),
    )
    op.create_index("ix_branch_user_memberships_branch_id", "branch_user_memberships", ["branch_id"])
    op.create_index("ix_branch_user_memberships_user_id", "branch_user_memberships", ["user_id"])

    # Preserve prior access: every existing company member keeps access to
    # every branch of that company. New grants are explicit.
    op.execute(sa.text("""
        INSERT INTO branch_user_memberships (branch_id, user_id, is_active)
        SELECT b.id, m.user_id, (m.is_active AND b.is_active)
        FROM branches AS b
        JOIN company_user_memberships AS m ON m.company_id = b.company_id
        ON CONFLICT (branch_id, user_id) DO NOTHING
    """))


def downgrade() -> None:
    op.drop_index("ix_branch_user_memberships_user_id", table_name="branch_user_memberships")
    op.drop_index("ix_branch_user_memberships_branch_id", table_name="branch_user_memberships")
    op.drop_table("branch_user_memberships")
