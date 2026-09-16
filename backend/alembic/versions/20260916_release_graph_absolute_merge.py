"""Converge the remaining independent release migration tails.

The earlier convergence migration already contains the accounting/tax,
fiscal-lifecycle, inventory-valuation and e-invoice tails.  The enterprise /
commissions branch is separate and ends at
``20260916_release_graph_inventory_commissions_merge``.

Only independent heads belong in this merge.  Enterprise-module integrity is
an ancestor of the inventory/commissions merge and therefore must not also be
listed as a parent.

Revision ID: 20260916_release_graph_absolute_merge
Revises: 20260916_release_graph_convergence, 20260916_release_graph_inventory_commissions_merge
"""

revision = "20260916_release_graph_absolute_merge"
down_revision = (
    "20260916_release_graph_convergence",
    "20260916_release_graph_inventory_commissions_merge",
)
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
