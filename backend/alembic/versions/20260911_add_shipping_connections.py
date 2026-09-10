"""Add secure shipping connection metadata.
Revision ID: 20260911shippingconn
Revises: 20260911shipping
"""
from alembic import op
import sqlalchemy as sa
revision = "20260911shippingconn"
down_revision = "20260911shipping"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("shipping_connections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider_id", sa.Integer(), sa.ForeignKey("shipping_providers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("environment", sa.String(20), nullable=False, server_default="production"),
        sa.Column("base_url", sa.String(500)),
        sa.Column("auth_type", sa.String(30), nullable=False, server_default="api_key"),
        sa.Column("secret_ref", sa.String(255)),
        sa.Column("account_reference", sa.String(150)),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("webhook_secret_ref", sa.String(255)),
        sa.Column("notes", sa.Text()),
        sa.Column("last_tested_at", sa.DateTime(timezone=True)),
        sa.Column("last_error", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "provider_id", "name", name="uq_shipping_connection_tenant_provider_name"))
    op.create_index("ix_shipping_connections_tenant_id", "shipping_connections", ["tenant_id"])
    op.create_index("ix_shipping_connections_provider_id", "shipping_connections", ["provider_id"])
    op.create_index("ix_shipping_connections_enabled", "shipping_connections", ["enabled"])

def downgrade():
    op.drop_index("ix_shipping_connections_enabled", table_name="shipping_connections")
    op.drop_index("ix_shipping_connections_provider_id", table_name="shipping_connections")
    op.drop_index("ix_shipping_connections_tenant_id", table_name="shipping_connections")
    op.drop_table("shipping_connections")
