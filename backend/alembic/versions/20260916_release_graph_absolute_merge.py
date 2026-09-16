"""Finalize the single release migration head.

The inventory/commissions merge is already an ancestor of the release
convergence migration through the enterprise -> inventory transaction /
accounting chain. It must therefore not be declared as a second parent here;
Alembic merges must list only independent heads.

Revision ID: 20260916_release_graph_absolute_merge
Revises: 20260916_release_graph_convergence
"""

revision = "20260916_release_graph_absolute_merge"
down_revision = "20260916_release_graph_convergence"
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
