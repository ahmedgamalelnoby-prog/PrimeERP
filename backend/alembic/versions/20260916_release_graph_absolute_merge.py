"""Converge every remaining release migration tail into one canonical head.

The release branch contains several historical merge migrations.  New feature
migrations were subsequently added on top of different tails, so the earlier
convergence migration does not cover the final enterprise and inventory/
commissions tails.  This migration is intentionally schema-neutral and exists
only to make the complete graph deterministic for fresh installs and upgrades.

Revision ID: 20260916_release_graph_absolute_merge
Revises: 20260916_release_graph_convergence, 20260916_enterprise_module_integrity, 20260916_release_graph_inventory_commissions_merge
"""

revision = "20260916_release_graph_absolute_merge"
down_revision = (
    "20260916_release_graph_convergence",
    "20260916_enterprise_module_integrity",
    "20260916_release_graph_inventory_commissions_merge",
)
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
