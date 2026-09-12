"""add transaction workflow permissions

Revision ID: 20260912_transaction_rbac
Revises: 20260912_subscription_rbac
"""

from alembic import op
import sqlalchemy as sa

revision = "20260912_transaction_rbac"
down_revision = "20260912_subscription_rbac"
branch_labels = None
depends_on = None

PERMISSIONS = (
    ("transaction.access", "transaction", "access"),
    ("transaction.write", "transaction", "write"),
    ("transaction.post", "transaction", "post"),
    ("transaction.reverse", "transaction", "reverse"),
)


def upgrade():
    bind = op.get_bind()
    permissions = sa.table(
        "permissions",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("resource", sa.String),
        sa.column("action", sa.String),
        sa.column("description", sa.String),
        sa.column("is_active", sa.Boolean),
    )
    for name, resource, action in PERMISSIONS:
        if bind.execute(sa.select(permissions.c.id).where(permissions.c.name == name)).first() is None:
            bind.execute(
                permissions.insert().values(
                    name=name,
                    resource=resource,
                    action=action,
                    description=f"{action.title()} transaction workflow records",
                    is_active=True,
                )
            )


def downgrade():
    bind = op.get_bind()
    permissions = sa.table("permissions", sa.column("name", sa.String))
    for name, _, _ in PERMISSIONS:
        bind.execute(permissions.delete().where(permissions.c.name == name))
