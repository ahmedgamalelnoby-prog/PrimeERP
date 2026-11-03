"""Add explicit user-to-company access assignments.

Revision ID: 20261110_user_company_access
Revises: 20261106_merge_inventory_approval_heads
"""
from alembic import op
import sqlalchemy as sa

revision = "20261110_user_company_access"
down_revision = "20261106_merge_inventory_approval_heads"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_company_access",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "company_id"),
    )
    op.create_index("ix_user_company_access_company_id", "user_company_access", ["company_id"])
    op.create_index(
        "uq_user_company_access_default",
        "user_company_access",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("is_default IS TRUE"),
    )
    op.execute(sa.text("""
        INSERT INTO user_company_access (user_id, company_id, is_default)
        SELECT user_id, company_id, (company_rank = 1)
        FROM (
            SELECT u.id AS user_id,
                   c.id AS company_id,
                   row_number() OVER (PARTITION BY u.id ORDER BY c.id) AS company_rank
            FROM users AS u
            JOIN companies AS c ON c.tenant_id = u.tenant_id
            WHERE u.tenant_id IS NOT NULL
              AND u.is_deleted IS FALSE
              AND c.is_active IS TRUE
        ) AS assignments
        ON CONFLICT (user_id, company_id) DO NOTHING
    """))


def downgrade():
    op.drop_index("uq_user_company_access_default", table_name="user_company_access")
    op.drop_index("ix_user_company_access_company_id", table_name="user_company_access")
    op.drop_table("user_company_access")
