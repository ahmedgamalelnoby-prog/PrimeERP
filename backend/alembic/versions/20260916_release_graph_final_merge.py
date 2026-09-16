"""Finalize the single release migration head.

The fiscal-year close guard is the descendant tail that already contains the
inventory integrity hardening revision in its ancestry. Therefore the older
inventory revision must not be declared as a second parent; Alembic merges
must list only independent heads.

Revision ID: 20260916_release_graph_final_merge
Revises: 20260916_fiscal_year_close_guard
"""

from alembic import op  # noqa: F401

revision = "20260916_release_graph_final_merge"
down_revision = "20260916_fiscal_year_close_guard"
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
