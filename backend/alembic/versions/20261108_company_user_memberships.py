"""Create explicit user-to-company access grants.

Existing tenant users retain the company access they had before this
restriction by receiving a membership for each company in their tenant.
"""
from alembic import op
import sqlalchemy as sa


revision = "20261108_company_user_memberships"
down_revision = "20261107_global_user_identity_uniqueness"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "company_user_memberships",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "company_id",
            sa.Integer(),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "assigned_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "company_id",
            "user_id",
            name="uq_company_user_membership",
        ),
    )
    op.create_index(
        "ix_company_user_memberships_company_id",
        "company_user_memberships",
        ["company_id"],
    )
    op.create_index(
        "ix_company_user_memberships_user_id",
        "company_user_memberships",
        ["user_id"],
    )

    # Preserve the previous tenant-wide company access for existing accounts.
    op.execute(sa.text("""
        INSERT INTO company_user_memberships
            (company_id, user_id, is_active)
        SELECT c.id, u.id, (u.is_active AND NOT u.is_deleted)
        FROM companies AS c
        JOIN users AS u ON u.tenant_id = c.tenant_id
        ON CONFLICT (company_id, user_id) DO NOTHING
    """))


def downgrade() -> None:
    op.drop_index(
        "ix_company_user_memberships_user_id",
        table_name="company_user_memberships",
    )
    op.drop_index(
        "ix_company_user_memberships_company_id",
        table_name="company_user_memberships",
    )
    op.drop_table("company_user_memberships")
