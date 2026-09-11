"""merge inventory RBAC and Salla webhook security heads

Revision ID: 20260911_security_inventory_merge
Revises: 20260911_salla_webhook_security, 20260911_shipping_settlement
"""

revision = "20260911_security_inventory_merge"
down_revision = ("20260911_salla_webhook_security", "20260911_shipping_settlement")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
