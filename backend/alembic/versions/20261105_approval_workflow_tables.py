"""Create approval request and approval step tables.

Revision ID: 20261105_approval_workflow_tables
Revises: 20261104_notification_messaging
"""
from alembic import op
import sqlalchemy as sa

revision = "20261105_approval_workflow_tables"
down_revision = "20261104_notification_messaging"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "approval_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("requested_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("mode", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("mode IN ('sequential','parallel','any_one')", name="ck_approval_requests_mode"),
        sa.CheckConstraint("status IN ('pending','approved','rejected','cancelled')", name="ck_approval_requests_status"),
    )
    op.create_index("ix_approval_requests_tenant_id", "approval_requests", ["tenant_id"])
    op.create_index("ix_approval_requests_company_id", "approval_requests", ["company_id"])

    op.create_table(
        "approval_steps",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("request_id", sa.Integer(), sa.ForeignKey("approval_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("approver_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("sequence_no", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("decided_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("request_id", "approver_user_id", name="uq_approval_step_request_approver"),
        sa.UniqueConstraint("request_id", "sequence_no", name="uq_approval_step_request_sequence"),
        sa.CheckConstraint("sequence_no > 0", name="ck_approval_steps_sequence"),
        sa.CheckConstraint("status IN ('pending','approved','rejected','skipped')", name="ck_approval_steps_status"),
    )
    op.create_index("ix_approval_steps_request_id", "approval_steps", ["request_id"])


def downgrade():
    op.drop_table("approval_steps")
    op.drop_table("approval_requests")
