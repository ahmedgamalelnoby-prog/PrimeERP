"""Distinguish plan-provisioned modules from explicit tenant overrides."""

from alembic import op
import sqlalchemy as sa

revision = "20260917_tenant_module_sources"
down_revision = "20260917_canonical_module_plan_bootstrap"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tenant_modules",
        sa.Column("source", sa.String(length=20), nullable=False, server_default="plan"),
    )
    op.create_check_constraint(
        "ck_tenant_module_source",
        "tenant_modules",
        "source IN ('plan', 'override')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_tenant_module_source", "tenant_modules", type_="check")
    op.drop_column("tenant_modules", "source")
