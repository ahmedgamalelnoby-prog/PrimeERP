from alembic import op
import sqlalchemy as sa

revision = "20260911_salla_sync_settings"
down_revision = "20260911_salla_mappings"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "salla_sync_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("connection_id", sa.Integer(), sa.ForeignKey("integration_connections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), sa.ForeignKey("inventory_warehouses.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("default_tax_rate_id", sa.Integer(), sa.ForeignKey("tax_rates.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("customer_code_prefix", sa.String(20), nullable=False, server_default="SALLA-C-"),
        sa.Column("product_code_prefix", sa.String(20), nullable=False, server_default="SALLA-P-"),
        sa.Column("import_paid_orders", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("auto_fulfill_orders", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.UniqueConstraint("connection_id", name="uq_salla_sync_settings_connection"),
    )
    op.create_index("ix_salla_sync_settings_connection_id", "salla_sync_settings", ["connection_id"], unique=True)


def downgrade():
    op.drop_index("ix_salla_sync_settings_connection_id", table_name="salla_sync_settings")
    op.drop_table("salla_sync_settings")
