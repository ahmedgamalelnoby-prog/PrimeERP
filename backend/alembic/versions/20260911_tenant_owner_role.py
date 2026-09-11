"""add tenant owner role for SaaS registrations

Revision ID: 20260911_tenant_owner_role
Revises: 20260911_production_heads_merge
"""

from alembic import op
import sqlalchemy as sa

revision = "20260911_tenant_owner_role"
down_revision = "20260911_production_heads_merge"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    roles = sa.table(
        "roles",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("description", sa.String),
        sa.column("is_active", sa.Boolean),
    )
    role_permissions = sa.table(
        "role_permissions",
        sa.column("role_id", sa.Integer),
        sa.column("permission_id", sa.Integer),
    )
    permissions = sa.table(
        "permissions",
        sa.column("id", sa.Integer),
        sa.column("is_active", sa.Boolean),
    )

    role_id = bind.execute(
        sa.select(roles.c.id).where(roles.c.name == "Tenant Owner")
    ).scalar()
    if role_id is None:
        role_id = bind.execute(
            roles.insert().values(
                name="Tenant Owner",
                description="Full operational access within the user's tenant",
                is_active=True,
            ).returning(roles.c.id)
        ).scalar_one()

    permission_ids = bind.execute(
        sa.select(permissions.c.id).where(permissions.c.is_active.is_(True))
    ).scalars().all()
    for permission_id in permission_ids:
        exists = bind.execute(
            sa.select(role_permissions.c.role_id).where(
                role_permissions.c.role_id == role_id,
                role_permissions.c.permission_id == permission_id,
            )
        ).first()
        if exists is None:
            bind.execute(
                role_permissions.insert().values(
                    role_id=role_id,
                    permission_id=permission_id,
                )
            )


def downgrade():
    bind = op.get_bind()
    roles = sa.table("roles", sa.column("id", sa.Integer), sa.column("name", sa.String))
    role_permissions = sa.table("role_permissions", sa.column("role_id", sa.Integer))
    role_id = bind.execute(
        sa.select(roles.c.id).where(roles.c.name == "Tenant Owner")
    ).scalar()
    if role_id is not None:
        bind.execute(role_permissions.delete().where(role_permissions.c.role_id == role_id))
        bind.execute(roles.delete().where(roles.c.id == role_id))
