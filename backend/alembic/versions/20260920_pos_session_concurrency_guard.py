"""prevent concurrent active POS sessions on the same terminal

Revision ID: 20260920_pos_session_concurrency_guard
Revises: 20260920_manufacturing_variance_approval
"""
from alembic import op
import sqlalchemy as sa

revision = "20260920_pos_session_concurrency_guard"
down_revision = "20260920_manufacturing_variance_approval"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "uq_pos_session_active_terminal",
        "pos_sessions",
        ["company_id", "terminal_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('open','closing')"),
    )


def downgrade():
    op.drop_index("uq_pos_session_active_terminal", table_name="pos_sessions")
