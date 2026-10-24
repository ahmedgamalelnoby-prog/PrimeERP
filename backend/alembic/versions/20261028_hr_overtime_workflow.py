"""Add overtime request and approval workflow."""
from alembic import op
import sqlalchemy as sa

revision = "20261028_hr_overtime_workflow"
down_revision = "20261027_hr_attendance_corrections"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "hr_overtime_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("attendance_record_id", sa.Integer(), sa.ForeignKey("hr_attendance_records.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("requested_hours", sa.Numeric(8, 2), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("submitted_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("decided_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("requested_hours > 0", name="ck_hr_overtime_request_hours"),
        sa.CheckConstraint("status IN ('pending','approved','rejected')", name="ck_hr_overtime_request_status"),
    )
    op.create_index("ix_hr_overtime_requests_company_id", "hr_overtime_requests", ["company_id"])
    op.create_index("ix_hr_overtime_requests_attendance_record_id", "hr_overtime_requests", ["attendance_record_id"])
    op.create_index(
        "ix_hr_overtime_request_status",
        "hr_overtime_requests",
        ["company_id", "status", "created_at"],
    )


def downgrade():
    op.drop_index("ix_hr_overtime_request_status", table_name="hr_overtime_requests")
    op.drop_index("ix_hr_overtime_requests_attendance_record_id", table_name="hr_overtime_requests")
    op.drop_index("ix_hr_overtime_requests_company_id", table_name="hr_overtime_requests")
    op.drop_table("hr_overtime_requests")
