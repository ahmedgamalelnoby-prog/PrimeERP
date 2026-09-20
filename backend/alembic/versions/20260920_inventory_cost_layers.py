"""Inventory cost layers for FIFO, weighted average and audit-ready costing."""
from alembic import op
import sqlalchemy as sa
revision="20260920_inventory_cost_layers";down_revision="20260920_accounting_automation";branch_labels=None;depends_on=None
def upgrade():
 op.create_table("inventory_cost_layers",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("company_id",sa.Integer(),sa.ForeignKey("companies.id",ondelete="CASCADE"),nullable=False),sa.Column("item_id",sa.Integer(),sa.ForeignKey("inventory_items.id",ondelete="RESTRICT"),nullable=False),sa.Column("warehouse_id",sa.Integer(),sa.ForeignKey("inventory_warehouses.id",ondelete="RESTRICT"),nullable=False),sa.Column("source_type",sa.String(40),nullable=False),sa.Column("source_id",sa.String(120),nullable=False),sa.Column("layer_date",sa.Date(),nullable=False),sa.Column("unit_cost",sa.Numeric(20,8),nullable=False),sa.Column("quantity_in",sa.Numeric(20,8),nullable=False,server_default="0"),sa.Column("quantity_out",sa.Numeric(20,8),nullable=False,server_default="0"),sa.Column("currency_code",sa.String(3),nullable=False,server_default="EGP"),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False))
 op.create_index("ix_inventory_cost_layers_lookup","inventory_cost_layers",["company_id","item_id","warehouse_id","layer_date"])
def downgrade():
 op.drop_index("ix_inventory_cost_layers_lookup",table_name="inventory_cost_layers");op.drop_table("inventory_cost_layers")
