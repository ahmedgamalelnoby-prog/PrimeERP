from alembic import op
import sqlalchemy as sa
revision="20260920_commerce_backorders"
down_revision="20260920_inventory_cost_revaluation"
branch_labels=None
depends_on=None
def upgrade():
 op.create_table("commerce_backorders",
  sa.Column("id",sa.Integer(),primary_key=True),sa.Column("company_id",sa.Integer(),sa.ForeignKey("companies.id",ondelete="CASCADE"),nullable=False),
  sa.Column("source_kind",sa.String(10),nullable=False),sa.Column("source_document_id",sa.Integer(),nullable=False),sa.Column("source_line_id",sa.Integer(),nullable=False),
  sa.Column("quantity",sa.Numeric(18,4),nullable=False),sa.Column("fulfilled_quantity",sa.Numeric(18,4),nullable=False,server_default="0"),sa.Column("status",sa.String(20),nullable=False,server_default="open"),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),
  sa.CheckConstraint("source_kind IN ('sale','purchase')",name="ck_backorder_kind"),sa.CheckConstraint("quantity > 0",name="ck_backorder_qty"),sa.CheckConstraint("fulfilled_quantity >= 0 AND fulfilled_quantity <= quantity",name="ck_backorder_fulfilled"),sa.CheckConstraint("status IN ('open','fulfilled','cancelled')",name="ck_backorder_status"),sa.UniqueConstraint("company_id","source_kind","source_line_id","status",name="uq_backorder_active_line"))
def downgrade(): op.drop_table("commerce_backorders")