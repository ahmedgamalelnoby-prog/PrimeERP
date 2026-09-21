"""manufacturing work-order and POS session completion"""
from alembic import op
import sqlalchemy as sa
revision="20260920_manufacturing_pos_completion"
down_revision="20260920_core_integration_contracts"
branch_labels=None
depends_on=None
def upgrade():
 op.create_table("pos_sessions",
  sa.Column("id",sa.Integer(),primary_key=True),
  sa.Column("tenant_id",sa.Integer(),sa.ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False),
  sa.Column("company_id",sa.Integer(),sa.ForeignKey("companies.id",ondelete="CASCADE"),nullable=False),
  sa.Column("terminal_id",sa.Integer(),sa.ForeignKey("pos_terminals.id",ondelete="RESTRICT"),nullable=False),
  sa.Column("cashier_id",sa.Integer(),sa.ForeignKey("users.id",ondelete="RESTRICT"),nullable=False),
  sa.Column("status",sa.String(20),nullable=False,server_default="open"),
  sa.Column("opened_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
  sa.Column("closed_at",sa.DateTime(timezone=True)),
  sa.Column("opening_cash",sa.Numeric(18,4),nullable=False,server_default="0"),
  sa.Column("expected_cash",sa.Numeric(18,4),nullable=False,server_default="0"),
  sa.Column("actual_cash",sa.Numeric(18,4)),
  sa.Column("difference",sa.Numeric(18,4)),
  sa.Column("notes",sa.Text()),
  sa.CheckConstraint("status IN ('open','closing','closed','cancelled')",name="ck_pos_session_status"),
  sa.CheckConstraint("opening_cash >= 0",name="ck_pos_session_opening_cash"))
 op.create_index("ix_pos_sessions_tenant_company","pos_sessions",["tenant_id","company_id"])
def downgrade():
 op.drop_index("ix_pos_sessions_tenant_company",table_name="pos_sessions")
 op.drop_table("pos_sessions")
