"""AI reporting automation tables on the enterprise-completion head."""
from alembic import op
import sqlalchemy as sa
revision="20260920_ai_reporting_automation"
down_revision="20260920_enterprise_finance"
branch_labels=None
depends_on=None
def upgrade():
    op.create_table("report_schedules",
        sa.Column("id",sa.Integer(),primary_key=True),
        sa.Column("tenant_id",sa.Integer(),sa.ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False),
        sa.Column("name",sa.String(160),nullable=False),
        sa.Column("report_key",sa.String(80),nullable=False),
        sa.Column("frequency",sa.String(20),nullable=False,server_default="monthly"),
        sa.Column("cron",sa.String(120)),
        sa.Column("timezone",sa.String(80),nullable=False,server_default="Africa/Cairo"),
        sa.Column("channels",sa.Text(),nullable=False,server_default='["email"]'),
        sa.Column("recipients",sa.Text(),nullable=False,server_default="[]"),
        sa.Column("filters",sa.Text(),nullable=False,server_default="{}"),
        sa.Column("format",sa.String(20),nullable=False,server_default="csv"),
        sa.Column("include_ai",sa.Boolean(),nullable=False,server_default=sa.true()),
        sa.Column("is_active",sa.Boolean(),nullable=False,server_default=sa.true()),
        sa.Column("next_run_at",sa.DateTime(timezone=True)),
        sa.Column("last_run_at",sa.DateTime(timezone=True)),
        sa.Column("created_at",sa.DateTime(),nullable=False,server_default=sa.func.now()),
        sa.Column("updated_at",sa.DateTime(),nullable=False,server_default=sa.func.now()))
    op.create_index("ix_report_schedules_tenant_id","report_schedules",["tenant_id"])
    op.create_index("ix_report_schedules_next_run_at","report_schedules",["next_run_at"])
    op.create_table("report_delivery_logs",
        sa.Column("id",sa.Integer(),primary_key=True),
        sa.Column("tenant_id",sa.Integer(),sa.ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False),
        sa.Column("schedule_id",sa.Integer(),sa.ForeignKey("report_schedules.id",ondelete="SET NULL")),
        sa.Column("report_key",sa.String(80),nullable=False),
        sa.Column("channel",sa.String(20),nullable=False),
        sa.Column("recipient",sa.String(320),nullable=False),
        sa.Column("status",sa.String(20),nullable=False),
        sa.Column("provider_message_id",sa.String(200)),
        sa.Column("error",sa.Text()),
        sa.Column("created_at",sa.DateTime(),nullable=False,server_default=sa.func.now()))
    op.create_index("ix_report_delivery_logs_tenant_id","report_delivery_logs",["tenant_id"])
    op.create_index("ix_report_delivery_logs_schedule_id","report_delivery_logs",["schedule_id"])
def downgrade():
    op.drop_index("ix_report_delivery_logs_schedule_id",table_name="report_delivery_logs")
    op.drop_index("ix_report_delivery_logs_tenant_id",table_name="report_delivery_logs")
    op.drop_table("report_delivery_logs")
    op.drop_index("ix_report_schedules_next_run_at",table_name="report_schedules")
    op.drop_index("ix_report_schedules_tenant_id",table_name="report_schedules")
    op.drop_table("report_schedules")
