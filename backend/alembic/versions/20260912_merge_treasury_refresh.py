"""merge treasury and refresh-token migration heads

Revision ID: 20260912_merge_treasury_refresh
Revises: 20260911_treasury, 20260912_refresh_tokens
"""

revision = "20260912_merge_treasury_refresh"
down_revision = ("20260911_treasury", "20260912_refresh_tokens")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
