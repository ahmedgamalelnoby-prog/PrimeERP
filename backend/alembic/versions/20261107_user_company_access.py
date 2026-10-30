"""Add explicit user-to-company access assignments.

Revision ID: 20261107_user_company_access
Revises: 20261106_merge_inventory_approval_heads
"""
from alembic import op
import sqlalchemy as sa


revision = "20261107_user_company_access"
down_revision = "20261106_merge_inventory_approval_heads"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "user_company_access" not in inspector.get_table_names():
        op.create_table(
            "user_company_access",
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        )

    op.execute(sa.text("""
        INSERT INTO user_company_access (user_id, company_id, is_default)
        SELECT ranked.user_id, ranked.company_id, ranked.position = 1
        FROM (
            SELECT u.id AS user_id,
                   c.id AS company_id,
                   ROW_NUMBER() OVER (PARTITION BY u.id ORDER BY c.id) AS position
            FROM users u
            JOIN companies c ON c.tenant_id = u.tenant_id
            WHERE u.tenant_id IS NOT NULL AND c.is_active IS TRUE
        ) AS ranked
        ON CONFLICT (user_id, company_id) DO NOTHING
    """))

    indexes = {index["name"] for index in sa.inspect(bind).get_indexes("user_company_access")}
    if "uq_user_company_access_one_default" not in indexes:
        op.create_index(
            "uq_user_company_access_one_default",
            "user_company_access",
            ["user_id"],
            unique=True,
            postgresql_where=sa.text("is_default IS TRUE"),
            sqlite_where=sa.text("is_default = 1"),
        )


def downgrade():
    bind = op.get_bind()
    if "user_company_access" in sa.inspect(bind).get_table_names():
        op.drop_table("user_company_access")
