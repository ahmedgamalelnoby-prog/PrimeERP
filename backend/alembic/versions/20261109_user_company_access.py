"""Create explicit user-to-company access assignments.

Existing non-deleted tenant users are granted access to every active company
in their tenant to preserve their former tenant-wide access. The first company
by ID is marked as the user's default company.
"""
from alembic import op
import sqlalchemy as sa


revision = "20261109_user_company_access"
down_revision = "20261108_merge_global_user_identity_heads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "user_company_access" not in inspector.get_table_names():
        op.create_table(
            "user_company_access",
            sa.Column(
                "user_id",
                sa.Integer(),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                primary_key=True,
                nullable=False,
            ),
            sa.Column(
                "company_id",
                sa.Integer(),
                sa.ForeignKey("companies.id", ondelete="CASCADE"),
                primary_key=True,
                nullable=False,
            ),
            sa.Column(
                "is_default",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
        )

    indexes = {
        index["name"]
        for index in sa.inspect(bind).get_indexes("user_company_access")
    }

    if "ix_user_company_access_company_id" not in indexes:
        op.create_index(
            "ix_user_company_access_company_id",
            "user_company_access",
            ["company_id"],
            unique=False,
        )

    if "uq_user_company_access_one_default" not in indexes:
        op.create_index(
            "uq_user_company_access_one_default",
            "user_company_access",
            ["user_id"],
            unique=True,
            postgresql_where=sa.text("is_default IS TRUE"),
        )

    # Preserve the tenant-wide access model users had before explicit
    # company assignments were introduced. Do not assign deleted users,
    # inactive companies, or platform users without a tenant.
    op.execute(
        sa.text(
            """
            INSERT INTO user_company_access (user_id, company_id, is_default)
            SELECT ranked.user_id, ranked.company_id, (ranked.position = 1)
            FROM (
                SELECT
                    u.id AS user_id,
                    c.id AS company_id,
                    ROW_NUMBER() OVER (
                        PARTITION BY u.id
                        ORDER BY c.id
                    ) AS position
                FROM users AS u
                JOIN companies AS c
                  ON c.tenant_id = u.tenant_id
                WHERE u.tenant_id IS NOT NULL
                  AND COALESCE(u.is_deleted, FALSE) IS FALSE
                  AND c.is_active IS TRUE
            ) AS ranked
            ON CONFLICT (user_id, company_id) DO NOTHING
            """
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    if "user_company_access" in sa.inspect(bind).get_table_names():
        op.drop_table("user_company_access")
