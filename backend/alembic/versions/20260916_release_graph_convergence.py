"""Converge all release migration heads into a single Alembic head.

This migration is intentionally schema-neutral. The three revisions listed in
``down_revision`` are independent release tails that must all be applied before
runtime startup can be considered migration-complete. Keeping them as explicit
parents preserves every schema operation while giving Alembic one canonical
release head for ``upgrade head``.

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
