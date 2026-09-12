"""add audit trail read permission

Revision ID: 20260912_audit_rbac
Revises: 20260912_egyptian_einvoice
"""

from alembic import op
import sqlalchemy as sa

revision = "20260912_audit_rbac"
down_revision = "20260912_egyptian_einvoice"
branch_labels = None
depends_on = None


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
    if bind.execute(sa.select(permissions.c.id).where(permissions.c.name == "audit.access")).first() is None:
        bind.execute(
            permissions.insert().values(
                name="audit.access",
                resource="audit",
                action="access",
                description="View security and business audit events",
                is_active=True,
            )
        )


def downgrade():
    bind = op.get_bind()
    permissions = sa.table("permissions", sa.column("id", sa.Integer), sa.column("name", sa.String))
    row = bind.execute(sa.select(permissions.c.id).where(permissions.c.name == "audit.access")).first()
    if row:
        role_permissions = sa.table("role_permissions", sa.column("permission_id", sa.Integer))
        bind.execute(role_permissions.delete().where(role_permissions.c.permission_id == row[0]))
        bind.execute(permissions.delete().where(permissions.c.id == row[0]))
