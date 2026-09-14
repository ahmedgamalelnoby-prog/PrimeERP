"""add integration product and variant mappings

Revision ID: 20260914_integration_product_mappings
Revises: 20260914_product_bundles
"""
from alembic import op
import sqlalchemy as sa

revision = "20260914_integration_product_mappings"
down_revision = "20260914_product_bundles"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "integration_product_mappings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("connection_id", sa.Integer(), sa.ForeignKey("integration_connections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("variant_id", sa.Integer(), sa.ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("external_id", sa.String(160), nullable=False),
        sa.Column("external_sku", sa.String(160), nullable=True),
        sa.Column("external_url", sa.String(500), nullable=True),
        sa.Column("sync_direction", sa.String(20), nullable=False, server_default="bidirectional"),
        sa.Column("sync_status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("connection_id", "external_id", name="uq_integration_product_mapping_external"),
        sa.UniqueConstraint("connection_id", "product_id", "variant_id", name="uq_integration_product_mapping_local"),
        sa.CheckConstraint("sync_direction IN ('inbound','outbound','bidirectional')", name="ck_integration_product_mapping_direction"),
        sa.CheckConstraint("sync_status IN ('active','paused','error','archived')", name="ck_integration_product_mapping_status"),
    )
    op.create_index("ix_integration_product_mappings_company", "integration_product_mappings", ["company_id"])
    op.create_index("ix_integration_product_mappings_connection_product", "integration_product_mappings", ["connection_id", "product_id"])
    op.create_index("ix_integration_product_mappings_connection_variant", "integration_product_mappings", ["connection_id", "variant_id"])


def downgrade():
    op.drop_index("ix_integration_product_mappings_connection_variant", table_name="integration_product_mappings")
    op.drop_index("ix_integration_product_mappings_connection_product", table_name="integration_product_mappings")
    op.drop_index("ix_integration_product_mappings_company", table_name="integration_product_mappings")
    op.drop_table("integration_product_mappings")
