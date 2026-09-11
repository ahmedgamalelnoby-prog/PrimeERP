"""merge shipping settlement and shipping RBAC migration heads

Revision ID: 20260911_shipping_heads_merge
Revises: 20260911_shipping_settlement, 20260911_shipping_rbac
"""

revision = "20260911_shipping_heads_merge"
down_revision = ("20260911_shipping_settlement", "20260911_shipping_rbac")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
