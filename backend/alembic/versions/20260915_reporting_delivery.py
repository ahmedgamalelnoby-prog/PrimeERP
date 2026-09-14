"""durable report definitions and outbound delivery attempts

Revision ID: 20260915_reporting_delivery
Revises: 20260915_jurisdiction_effective_date_guards
"""
from alembic import op
import sqlalchemy as sa

revision = "20260915_reporting_delivery"
down_revision = "20260915_jurisdiction_effective_date_guards"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("report_definitions", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False), sa.Column("code", sa.String(100), nullable=False), sa.Column("name", sa.String(255), nullable=False), sa.Column("report_type", sa.String(50), nullable=False, server_default="custom"), sa.Column("parameters_json", sa.Text(), nullable=False, server_default="{}"), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_index("ix_report_definitions_company_id", "report_definitions", ["company_id"])
    op.create_index("ix_report_definitions_code", "report_definitions", ["code"])
    op.create_index("ix_report_definitions_is_active", "report_definitions", ["is_active"])
    op.create_unique_constraint("uq_report_definitions_company_code", "report_definitions", ["company_id", "code"])

    op.create_table("report_deliveries", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False), sa.Column("report_definition_id", sa.Integer(), sa.ForeignKey("report_definitions.id", ondelete="CASCADE"), nullable=False), sa.Column("channel", sa.String(30), nullable=False), sa.Column("destination", sa.String(320), nullable=False), sa.Column("schedule", sa.String(120), nullable=False), sa.Column("format", sa.String(20), nullable=False, server_default="json"), sa.Column("filters_json", sa.Text(), nullable=False, server_default="{}"), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("last_run_at", sa.DateTime(timezone=True)), sa.Column("next_run_at", sa.DateTime(timezone=True)), sa.Column("last_status", sa.String(30)), sa.Column("last_error", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_index("ix_report_deliveries_company_id", "report_deliveries", ["company_id"])
    op.create_index("ix_report_deliveries_report_definition_id", "report_deliveries", ["report_definition_id"])
    op.create_index("ix_report_deliveries_is_active", "report_deliveries", ["is_active"])
    op.create_index("ix_report_deliveries_next_run_at", "report_deliveries", ["next_run_at"])
    op.create_check_constraint("ck_report_delivery_channel", "report_deliveries", "channel IN ('email','whatsapp')")
    op.create_check_constraint("ck_report_delivery_format", "report_deliveries", "format IN ('json','text')")

    op.create_table("report_delivery_attempts", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("delivery_id", sa.Integer(), sa.ForeignKey("report_deliveries.id", ondelete="CASCADE"), nullable=False), sa.Column("attempt_no", sa.Integer(), nullable=False), sa.Column("status", sa.String(30), nullable=False), sa.Column("response_code", sa.Integer()), sa.Column("response_reference", sa.String(255)), sa.Column("error_message", sa.Text()), sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_index("ix_report_delivery_attempts_delivery_id", "report_delivery_attempts", ["delivery_id"])
    op.create_check_constraint("ck_report_delivery_attempt_no_positive", "report_delivery_attempts", "attempt_no > 0")


def downgrade():
    op.drop_table("report_delivery_attempts")
    op.drop_table("report_deliveries")
    op.drop_table("report_definitions")
