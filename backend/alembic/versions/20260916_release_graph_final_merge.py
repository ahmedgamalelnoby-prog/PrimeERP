"""Merge the current accounting/tax and inventory migration tails.

This merge migration intentionally contains no schema operations. It exists to
make the release graph converge before runtime migration validation.

Revision ID: 20260916_release_graph_final_merge
Revises: 20260916_fiscal_year_close_guard, 20260915_inventory_integrity_hardening
"""

from alembic import op  # noqa: F401

revision = "20260916_release_graph_final_merge"
down_revision = (
    "20260916_fiscal_year_close_guard",
    "20260915_inventory_integrity_hardening",
)
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
