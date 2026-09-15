"""Harden SaaS lifecycle and module effective-date integrity.

Revision ID: 20260915_saas_lifecycle_integrity
Revises: 20260915_commerce_payment_integrity
"""
from alembic import op
import sqlalchemy as sa

revision = "20260915_saas_lifecycle_integrity"
down_revision = "20260915_commerce_payment_integrity"
branch_labels = None
depends_on = None


def _preflight(conn):
    checks = [
        (
            "tenants trial dates",
            """
            SELECT 1 FROM tenants
            WHERE trial_started_at IS NOT NULL
              AND trial_ends_at IS NOT NULL
              AND trial_ends_at < trial_started_at
            LIMIT 1
            """,
        ),
        (
            "subscriptions dates",
            """
            SELECT 1 FROM subscriptions
            WHERE ends_at IS NOT NULL
              AND ends_at < starts_at
            LIMIT 1
            """,
        ),
        (
            "subscriptions trial dates",
            """
            SELECT 1 FROM subscriptions
            WHERE trial_ends_at IS NOT NULL
              AND trial_ends_at < starts_at
            LIMIT 1
            """,
        ),
        (
            "subscription trial end after subscription end",
            """
            SELECT 1 FROM subscriptions
            WHERE trial_ends_at IS NOT NULL
              AND ends_at IS NOT NULL
              AND trial_ends_at > ends_at
            LIMIT 1
            """,
        ),
        (
            "tenant module dates",
            """
            SELECT 1 FROM tenant_modules
            WHERE starts_at IS NOT NULL
              AND ends_at IS NOT NULL
              AND ends_at < starts_at
            LIMIT 1
            """,
        ),
    ]
    for label, sql in checks:
        if conn.execute(sa.text(sql)).first() is not None:
            raise RuntimeError(f"Preflight failed: {label} contains invalid effective dates")


def upgrade():
    conn = op.get_bind()
    _preflight(conn)

    op.create_check_constraint(
        "ck_tenant_trial_dates",
        "tenants",
        "trial_ends_at IS NULL OR trial_started_at IS NULL OR trial_ends_at >= trial_started_at",
    )
    op.create_check_constraint(
        "ck_subscription_effective_dates",
        "subscriptions",
        "ends_at IS NULL OR ends_at >= starts_at",
    )
    op.create_check_constraint(
        "ck_subscription_trial_dates",
        "subscriptions",
        "trial_ends_at IS NULL OR trial_ends_at >= starts_at",
    )
    op.create_check_constraint(
        "ck_subscription_trial_within_end",
        "subscriptions",
        "ends_at IS NULL OR trial_ends_at IS NULL OR trial_ends_at <= ends_at",
    )
    op.create_check_constraint(
        "ck_tenant_module_effective_dates",
        "tenant_modules",
        "ends_at IS NULL OR starts_at IS NULL OR ends_at >= starts_at",
    )


def downgrade():
    op.drop_constraint("ck_tenant_module_effective_dates", "tenant_modules", type_="check")
    op.drop_constraint("ck_subscription_trial_within_end", "subscriptions", type_="check")
    op.drop_constraint("ck_subscription_trial_dates", "subscriptions", type_="check")
    op.drop_constraint("ck_subscription_effective_dates", "subscriptions", type_="check")
    op.drop_constraint("ck_tenant_trial_dates", "tenants", type_="check")
