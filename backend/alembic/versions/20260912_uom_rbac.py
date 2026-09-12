"""add UOM API permissions

Revision ID: 20260912_uom_rbac
Revises: 20260912_transaction_rbac
"""

from alembic import op
import sqlalchemy as sa

revision = "20260912_uom_rbac"
down_revision = "20260912_transaction_rbac"
branch_labels = None
depends_on = None

PERMISSIONS = (
    ("uom.access", "uom", "access"),
    ("uom.write", "uom", "write"),
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
                    description=f"{action.title()} units of measure",
                    is_active=True,
                )
            )


def downgrade():
    bind = op.get_bind()
    permissions = sa.table(
        "permissions",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
    )
    permission_ids = [
        row[0]
        for row in bind.execute(
            sa.select(permissions.c.id).where(permissions.c.name.in_([p[0] for p in PERMISSIONS]))
        ).all()
    ]
    if permission_ids:
        role_permissions = sa.table(
            "role_permissions",
            sa.column("permission_id", sa.Integer),
        )
        bind.execute(role_permissions.delete().where(role_permissions.c.permission_id.in_(permission_ids)))
        bind.execute(permissions.delete().where(permissions.c.id.in_(permission_ids)))
