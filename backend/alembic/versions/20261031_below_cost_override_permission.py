"""Register the explicit below-cost sales override permission.

Revision ID: 20261031_below_cost_override_permission
Revises: 20261030_manufacturing_work_orders, 20260920_enterprise_finance
"""
from alembic import op
import sqlalchemy as sa


revision = "20261031_below_cost_override_permission"
down_revision = ("20261030_manufacturing_work_orders", "20260920_enterprise_finance")
branch_labels = None
depends_on = None


def upgrade():
    permissions = sa.table(
        "permissions",
        sa.column("id", sa.Integer()),
        sa.column("name", sa.String(100)),
        sa.column("resource", sa.String(100)),
        sa.column("action", sa.String(50)),
        sa.column("description", sa.String(255)),
        sa.column("is_active", sa.Boolean()),
    )
    exists = sa.exists(
        sa.select(sa.literal(1)).select_from(permissions).where(
            permissions.c.name == "commerce.below_cost_override"
        )
    )
    row = sa.select(
        sa.literal("commerce.below_cost_override"),
        sa.literal("commerce"),
        sa.literal("below_cost_override"),
        sa.literal("Authorize sales delivery posting below inventory cost"),
        sa.literal(True),
    ).where(~exists)
    op.execute(sa.insert(permissions).from_select(
        ["name", "resource", "action", "description", "is_active"],
        row,
    ))


def downgrade():
    permissions = sa.table(
        "permissions",
        sa.column("id", sa.Integer()),
        sa.column("name", sa.String(100)),
    )
    role_permissions = sa.table(
        "role_permissions",
        sa.column("permission_id", sa.Integer()),
    )
    assigned = sa.exists(
        sa.select(sa.literal(1)).select_from(role_permissions).where(
            role_permissions.c.permission_id == permissions.c.id
        )
    )
    op.execute(
        sa.delete(permissions).where(
            permissions.c.name == "commerce.below_cost_override",
            ~assigned,
        )
    )
