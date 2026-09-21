"""add missing Purchasing and Treasury RBAC permissions.

Revision ID: 20260921_purchasing_treasury_rbac
Revises: 20260921_align_saas_module_catalog
"""

from alembic import op
import sqlalchemy as sa

revision = "20260921_purchasing_treasury_rbac"
down_revision = "20260921_align_saas_module_catalog"
branch_labels = None
depends_on = None

PERMISSIONS = (
    ("purchasing.access", "purchasing", "access"),
    ("purchasing.write", "purchasing", "write"),
    ("purchasing.post", "purchasing", "post"),
    ("treasury.access", "treasury", "access"),
    ("treasury.write", "treasury", "write"),
    ("treasury.post", "treasury", "post"),
    ("treasury.reverse", "treasury", "reverse"),
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
    bind.execute(
        permissions.delete().where(
            permissions.c.name.in_([name for name, _, _ in PERMISSIONS])
        )
    )
