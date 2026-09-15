"""Harden tax-rate domain invariants.

Revision ID: 20260915_tax_rate_domain_hardening
Revises: 20260915_release_heads_final_merge
"""
from alembic import op
import sqlalchemy as sa

revision = "20260915_tax_rate_domain_hardening"
down_revision = "20260915_release_heads_final_merge"
branch_labels = None
depends_on = None


def _assert_clean(conn, sql: str, message: str) -> None:
    if conn.execute(sa.text(sql)).scalar():
        raise RuntimeError(message)


def upgrade():
    conn = op.get_bind()

    _assert_clean(
        conn,
        "SELECT EXISTS (SELECT 1 FROM tax_rates WHERE rate < 0 OR rate > 100)",
        "Cannot harden tax_rates: one or more rates are outside 0..100 percent.",
    )
    _assert_clean(
        conn,
        "SELECT EXISTS (SELECT 1 FROM tax_rates WHERE tax_type NOT IN ('vat','wht','sales_tax','purchase_tax','excise','custom'))",
        "Cannot harden tax_rates: unsupported tax_type values exist.",
    )

    op.create_check_constraint(
        "ck_tax_rate_percent_range",
        "tax_rates",
        "rate >= 0 AND rate <= 100",
    )
    op.create_check_constraint(
        "ck_tax_rate_type",
        "tax_rates",
        "tax_type IN ('vat','wht','sales_tax','purchase_tax','excise','custom')",
    )


def downgrade():
    op.drop_constraint("ck_tax_rate_type", "tax_rates", type_="check")
    op.drop_constraint("ck_tax_rate_percent_range", "tax_rates", type_="check")
