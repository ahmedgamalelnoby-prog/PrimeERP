"""Harden SaaS subscription limits for product-level overrides.

This is additive and preserves all existing subscription values.
"""

from alembic import op
import sqlalchemy as sa

revision = "20260917_saas_functional_hardening"
down_revision = "20260917_tenant_module_sources"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("subscriptions", sa.Column("custom_max_products", sa.Integer(), nullable=True))
    op.create_check_constraint(
        "ck_subscription_custom_max_products",
        "subscriptions",
        "custom_max_products IS NULL OR custom_max_products >= 1",
    )


def downgrade() -> None:
    op.drop_constraint("ck_subscription_custom_max_products", "subscriptions", type_="check")
    op.drop_column("subscriptions", "custom_max_products")
