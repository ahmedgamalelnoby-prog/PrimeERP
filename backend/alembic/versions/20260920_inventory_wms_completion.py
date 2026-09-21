"""Complete inventory WMS execution, tracking and cycle-count controls."""
from alembic import op
import sqlalchemy as sa

revision = "20260920_inventory_wms_completion"
down_revision = "20260920_treasury_core_completion"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "inventory_wms_operations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), sa.ForeignKey("inventory_warehouses.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("operation_type", sa.String(20), nullable=False),
        sa.Column("reference", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("notes", sa.Text()),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("posted_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("company_id","reference",name="uq_inventory_wms_operation_reference"),
        sa.CheckConstraint("operation_type IN ('receiving','putaway','picking','packing','dispatch','cycle_count')",name="ck_inventory_wms_operation_type"),
        sa.CheckConstraint("status IN ('draft','approved','in_progress','completed','cancelled')",name="ck_inventory_wms_operation_status"),
    )
    op.create_index("ix_inventory_wms_operations_company","inventory_wms_operations",["company_id"])
    op.create_index("ix_inventory_wms_operations_warehouse","inventory_wms_operations",["warehouse_id"])
    op.create_table(
        "inventory_wms_operation_lines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("operation_id", sa.Integer(), sa.ForeignKey("inventory_wms_operations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_id", sa.Integer(), sa.ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("variant_id", sa.Integer(), sa.ForeignKey("product_variants.id", ondelete="RESTRICT")),
        sa.Column("source_location_id", sa.Integer(), sa.ForeignKey("inventory_locations.id", ondelete="RESTRICT")),
        sa.Column("destination_location_id", sa.Integer(), sa.ForeignKey("inventory_locations.id", ondelete="RESTRICT")),
        sa.Column("quantity", sa.Numeric(18,4), nullable=False),
        sa.Column("processed_quantity", sa.Numeric(18,4), nullable=False, server_default="0"),
        sa.Column("unit_cost", sa.Numeric(18,4), nullable=False, server_default="0"),
        sa.Column("lot_number", sa.String(100)),
        sa.Column("serial_number", sa.String(100)),
        sa.Column("expiry_date", sa.Date()),
        sa.Column("barcode", sa.String(100)),
        sa.Column("stock_move_id", sa.Integer(), sa.ForeignKey("inventory_stock_moves.id", ondelete="RESTRICT"), unique=True),
        sa.Column("count_expected", sa.Numeric(18,4)),
        sa.Column("count_actual", sa.Numeric(18,4)),
        sa.CheckConstraint("quantity > 0",name="ck_inventory_wms_line_quantity"),
        sa.CheckConstraint("processed_quantity >= 0 AND processed_quantity <= quantity",name="ck_inventory_wms_line_processed"),
        sa.CheckConstraint("unit_cost >= 0",name="ck_inventory_wms_line_cost"),
        sa.CheckConstraint("serial_number IS NULL OR quantity = 1",name="ck_inventory_wms_serial_one"),
    )
    op.create_index("ix_inventory_wms_lines_item","inventory_wms_operation_lines",["item_id"])
    op.create_table(
        "inventory_tracking_units",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_id", sa.Integer(), sa.ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("variant_id", sa.Integer(), sa.ForeignKey("product_variants.id", ondelete="RESTRICT")),
        sa.Column("warehouse_id", sa.Integer(), sa.ForeignKey("inventory_warehouses.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("location_id", sa.Integer(), sa.ForeignKey("inventory_locations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("lot_number", sa.String(100)),
        sa.Column("serial_number", sa.String(100)),
        sa.Column("expiry_date", sa.Date()),
        sa.Column("barcode", sa.String(100)),
        sa.Column("quantity", sa.Numeric(18,4), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.CheckConstraint("quantity >= 0",name="ck_inventory_tracking_unit_quantity"),
        sa.UniqueConstraint("company_id","item_id","variant_id","location_id","lot_number","serial_number",name="uq_inventory_tracking_unit_identity"),
    )
    for col in ("item_id","variant_id","location_id","lot_number","serial_number","expiry_date","barcode"):
        op.create_index(f"ix_inventory_tracking_{col}","inventory_tracking_units",[col])

def downgrade():
    for name in ["ix_inventory_tracking_barcode","ix_inventory_tracking_expiry_date","ix_inventory_tracking_serial_number","ix_inventory_tracking_lot_number","ix_inventory_tracking_location_id","ix_inventory_tracking_variant_id","ix_inventory_tracking_item_id"]:
        op.drop_index(name,table_name="inventory_tracking_units")
    op.drop_table("inventory_tracking_units")
    op.drop_index("ix_inventory_wms_lines_item",table_name="inventory_wms_operation_lines")
    op.drop_table("inventory_wms_operation_lines")
    op.drop_index("ix_inventory_wms_operations_warehouse",table_name="inventory_wms_operations")
    op.drop_index("ix_inventory_wms_operations_company",table_name="inventory_wms_operations")
    op.drop_table("inventory_wms_operations")
