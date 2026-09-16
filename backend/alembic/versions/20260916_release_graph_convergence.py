"""Converge all release migration heads into a single Alembic head.

This migration is intentionally schema-neutral. The release branch accumulated
multiple independent tails after the earlier release-head merges. Only the
actual independent heads are listed below; ancestor revisions must not also be
listed because Alembic advances those revisions through their descendant head.

Revision ID: 20260916_release_graph_convergence
Revises: 20260916_einvoice_tenant_integrity, 20260916_fiscal_lifecycle_guards, 20260916_inventory_valuation_audit
"""

from alembic import op  # noqa: F401

revision = "20260916_release_graph_convergence"
down_revision = (
    "20260916_einvoice_tenant_integrity",
    "20260916_fiscal_lifecycle_guards",
    "20260916_inventory_valuation_audit",
)
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
