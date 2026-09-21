from alembic import op
import sqlalchemy as sa
revision="20260920_core_integration_contracts"
down_revision="20260920_treasury_core_completion"
branch_labels=None
depends_on=None
def upgrade():
 op.create_table("integration_transactions",sa.Column("id",sa.Integer,primary_key=True),sa.Column("tenant_id",sa.Integer,sa.ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False),sa.Column("company_id",sa.Integer,sa.ForeignKey("companies.id",ondelete="CASCADE"),nullable=False),sa.Column("source_module",sa.String(80),nullable=False),sa.Column("source_entity",sa.String(120),nullable=False),sa.Column("source_id",sa.String(120),nullable=False),sa.Column("operation",sa.String(80),nullable=False),sa.Column("idempotency_key",sa.String(180),nullable=False),sa.Column("status",sa.String(30),nullable=False,server_default="completed"),sa.Column("reversal_of_id",sa.Integer,sa.ForeignKey("integration_transactions.id",ondelete="RESTRICT")),sa.Column("reason",sa.Text),sa.Column("actor_id",sa.Integer,sa.ForeignKey("users.id",ondelete="SET NULL")),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.func.now()),sa.Column("reversed",sa.Boolean,nullable=False,server_default=sa.false()),sa.UniqueConstraint("company_id","idempotency_key",name="uq_integration_tx_idempotency"));op.create_index("ix_integration_transactions_company_source","integration_transactions",["company_id","source_module","source_entity","source_id"])
def downgrade():op.drop_index("ix_integration_transactions_company_source",table_name="integration_transactions");op.drop_table("integration_transactions")
