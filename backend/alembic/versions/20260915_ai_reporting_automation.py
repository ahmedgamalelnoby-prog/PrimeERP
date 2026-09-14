"""AI analytics, report scheduling and delivery audit tables.

Revision ID: 20260915_ai_reporting_automation
Revises: 20260915_jurisdiction_effective_date_guards
"""
from alembic import op
import sqlalchemy as sa

revision = "20260915_ai_reporting_automation"
down_revision = "20260915_jurisdiction_effective_date_guards"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "report_schedules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("report_key", sa.String(length=80), nullable=False),
        sa.Column("frequency", sa.String(length=20), nullable=False, server_default="monthly"),
        sa.Column("cron", sa.String(length=120), nullable=True),
        sa.Column("timezone", sa.String(length=80), nullable=False, server_default="Africa/Cairo"),
        sa.Column("channels", sa.Text(), nullable=False, server_default='["email"]'),
        sa.Column("recipients", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("filters", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("format", sa.String(length=20), nullable=False, server_default="csv"),
        sa.Column("include_ai", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_report_schedules_tenant_id", "report_schedules", ["tenant_id"])
    op.create_index("ix_report_schedules_next_run_at", "report_schedules", ["next_run_at"])

    op.create_table(
        "report_delivery_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("schedule_id", sa.Integer(), sa.ForeignKey("report_schedules.id", ondelete="SET NULL"), nullable=True),
        sa.Column("report_key", sa.String(length=80), nullable=False),
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column("recipient", sa.String(length=320), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("provider_message_id", sa.String(length=200), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_report_delivery_logs_tenant_id", "report_delivery_logs", ["tenant_id"])
    op.create_index("ix_report_delivery_logs_schedule_id", "report_delivery_logs", ["schedule_id"])


def downgrade():
    op.drop_index("ix_report_delivery_logs_schedule_id", table_name="report_delivery_logs")
    op.drop_index("ix_report_delivery_logs_tenant_id", table_name="report_delivery_logs")
    op.drop_table("report_delivery_logs")
    op.drop_index("ix_report_schedules_next_run_at", table_name="report_schedules")
    op.drop_index("ix_report_schedules_tenant_id", table_name="report_schedules")
    op.drop_table("report_schedules")
