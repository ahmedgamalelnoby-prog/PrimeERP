"""add tenant subscription management permission

Revision ID: 20260912_subscription_rbac
Revises: 20260912_merge_treasury_refresh
"""

from alembic import op
import sqlalchemy as sa

revision = "20260912_subscription_rbac"
down_revision = "20260912_merge_treasury_refresh"
branch_labels = None
depends_on = None

PERMISSION = ("subscription.manage", "subscription", "manage")


def upgrade():
    bind = op.get_bind()
    permissions = sa.table(
        "permissions",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("resource", sa.String),
        sa.column("action", sa.String),
        sa.column("is_active", sa.Boolean),
    )
    if bind.execute(sa.select(permissions.c.id).where(permissions.c.name == PERMISSION[0])).first() is None:
        bind.execute(
            permissions.insert().values(
                name=PERMISSION[0],
                resource=PERMISSION[1],
                action=PERMISSION[2],
                is_active=True,
            )
        )


def downgrade():
    bind = op.get_bind()
    permissions = sa.table("permissions", sa.column("name", sa.String))
    bind.execute(permissions.delete().where(permissions.c.name == PERMISSION[0]))
