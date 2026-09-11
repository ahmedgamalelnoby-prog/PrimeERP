"""seed Shipping API permissions

Revision ID: 20260911_shipping_rbac
Revises: 20260911_shipping_payment_account
"""
from alembic import op
import sqlalchemy as sa

revision = "20260911_shipping_rbac"
down_revision = "20260911_shipping_payment_account"
branch_labels = None
depends_on = None

PERMISSIONS = (
    ("shipping.access", "shipping", "access"),
    ("shipping.write", "shipping", "write"),
    ("shipping.post", "shipping", "post"),
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
        if bind.execute(sa.select(permissions.c.id).where(permissions.c.name == name)).first() is None:
            bind.execute(permissions.insert().values(name=name, resource=resource, action=action, is_active=True))


def downgrade():
    bind = op.get_bind()
    permissions = sa.table("permissions", sa.column("name", sa.String))
    bind.execute(permissions.delete().where(permissions.c.name.in_([p[0] for p in PERMISSIONS])))
