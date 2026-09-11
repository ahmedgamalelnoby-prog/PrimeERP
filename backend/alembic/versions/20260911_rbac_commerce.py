"""seed Commerce API permissions

Revision ID: 20260911_rbac_commerce
Revises: 20260911_inventory_fifo_layers
"""
from alembic import op
import sqlalchemy as sa

revision = "20260911_rbac_commerce"
down_revision = "20260911_inventory_fifo_layers"
branch_labels = None
depends_on = None

PERMISSIONS = (
    ("commerce.access", "commerce", "access"),
    ("commerce.write", "commerce", "write"),
    ("commerce.post", "commerce", "post"),
    ("commerce.payment", "commerce", "payment"),
    ("commerce.reverse", "commerce", "reverse"),
)


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
    for name, resource, action in PERMISSIONS:
        exists = bind.execute(
            sa.select(permissions.c.id).where(permissions.c.name == name)
        ).first()
        if exists is None:
            bind.execute(
                permissions.insert().values(
                    name=name,
                    resource=resource,
                    action=action,
                    is_active=True,
                )
            )


def downgrade():
    bind = op.get_bind()
    permissions = sa.table("permissions", sa.column("name", sa.String))
    bind.execute(permissions.delete().where(permissions.c.name.in_([p[0] for p in PERMISSIONS])))
