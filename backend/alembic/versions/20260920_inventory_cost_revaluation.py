from alembic import op
import sqlalchemy as sa
revision="20260920_inventory_cost_revaluation"
down_revision="20260920_inventory_wms_completion"
branch_labels=None
depends_on=None
def upgrade():
    op.create_table("inventory_cost_revaluations",
      sa.Column("id",sa.Integer(),primary_key=True),sa.Column("company_id",sa.Integer(),sa.ForeignKey("companies.id",ondelete="CASCADE"),nullable=False),
      sa.Column("item_id",sa.Integer(),sa.ForeignKey("inventory_items.id",ondelete="RESTRICT"),nullable=False),sa.Column("warehouse_id",sa.Integer(),sa.ForeignKey("inventory_warehouses.id",ondelete="RESTRICT"),nullable=False),
      sa.Column("effective_date",sa.Date(),nullable=False),sa.Column("old_unit_cost",sa.Numeric(18,4),nullable=False),sa.Column("new_unit_cost",sa.Numeric(18,4),nullable=False),sa.Column("quantity",sa.Numeric(18,4),nullable=False),sa.Column("delta_value",sa.Numeric(18,4),nullable=False),sa.Column("reason",sa.Text(),nullable=False),sa.Column("status",sa.String(20),nullable=False,server_default="draft"),sa.Column("journal_entry_id",sa.Integer(),sa.ForeignKey("journal_entries.id",ondelete="RESTRICT")),sa.Column("created_by",sa.Integer(),sa.ForeignKey("users.id",ondelete="SET NULL")),sa.Column("posted_by",sa.Integer(),sa.ForeignKey("users.id",ondelete="SET NULL")),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),sa.Column("posted_at",sa.DateTime(timezone=True)),
      sa.CheckConstraint("new_unit_cost >= 0",name="ck_inventory_reval_new_cost"),sa.CheckConstraint("quantity >= 0",name="ck_inventory_reval_quantity"),sa.CheckConstraint("status IN ('draft','posted','cancelled')",name="ck_inventory_reval_status"))
    op.create_index("ix_inventory_reval_company_item_warehouse","inventory_cost_revaluations",["company_id","item_id","warehouse_id"])
def downgrade():
    op.drop_index("ix_inventory_reval_company_item_warehouse",table_name="inventory_cost_revaluations");op.drop_table("inventory_cost_revaluations")
