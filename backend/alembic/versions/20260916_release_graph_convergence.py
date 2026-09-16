"""Converge all release migration heads into a single Alembic head.

This migration is intentionally schema-neutral. The release branch accumulated
multiple independent tails after the earlier release-head merges. Every tail is
listed explicitly below so ``upgrade head`` applies every schema operation once
and leaves exactly one canonical Alembic head.

Revision ID: 20260916_release_graph_convergence
Revises: 20260916_einvoice_tenant_integrity, 20260916_fiscal_lifecycle_guards, 20260916_inventory_valuation_audit, 20260915_einvoice_idempotency, 20260916_tax_return_tenant_integrity
"""

from alembic import op  # noqa: F401

revision = "20260916_release_graph_convergence"
down_revision = (
    "20260916_einvoice_tenant_integrity",
    "20260916_fiscal_lifecycle_guards",
    "20260916_inventory_valuation_audit",
    "20260915_einvoice_idempotency",
    "20260916_tax_return_tenant_integrity",
)
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
