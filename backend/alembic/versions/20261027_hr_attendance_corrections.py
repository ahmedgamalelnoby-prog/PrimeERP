"""Add attendance records and correction approvals."""
from alembic import op
import sqlalchemy as sa

revision = "20261027_hr_attendance_corrections"
down_revision = "20261026_hr_leave_workflow"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "hr_attendance_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("attendance_date", sa.Date(), nullable=False),
        sa.Column("source", sa.String(length=20), nullable=False, server_default="manual"),
        sa.Column("check_in_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("check_out_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recorded_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("company_id", "employee_id", "attendance_date", name="uq_hr_attendance_employee_date"),
        sa.CheckConstraint("source IN ('manual','biometric','mobile','integration')", name="ck_hr_attendance_source"),
        sa.CheckConstraint("check_out_at IS NULL OR check_out_at > check_in_at", name="ck_hr_attendance_time_order"),
    )
    op.create_index("ix_hr_attendance_records_company_id", "hr_attendance_records", ["company_id"])
    op.create_index("ix_hr_attendance_records_employee_id", "hr_attendance_records", ["employee_id"])
    op.create_index("ix_hr_attendance_company_date", "hr_attendance_records", ["company_id", "attendance_date"])

    op.create_table(
        "hr_attendance_corrections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("attendance_record_id", sa.Integer(), sa.ForeignKey("hr_attendance_records.id", ondelete="CASCADE"), nullable=False),
        sa.Column("proposed_check_in_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("proposed_check_out_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("submitted_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("decided_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('pending','approved','rejected')", name="ck_hr_attendance_correction_status"),
        sa.CheckConstraint("proposed_check_out_at IS NULL OR proposed_check_out_at > proposed_check_in_at", name="ck_hr_attendance_correction_time_order"),
    )
    op.create_index("ix_hr_attendance_corrections_company_id", "hr_attendance_corrections", ["company_id"])
    op.create_index("ix_hr_attendance_corrections_attendance_record_id", "hr_attendance_corrections", ["attendance_record_id"])
    op.create_index(
        "ix_hr_attendance_correction_status",
        "hr_attendance_corrections",
        ["company_id", "status", "created_at"],
    )


def downgrade():
    op.drop_index("ix_hr_attendance_correction_status", table_name="hr_attendance_corrections")
    op.drop_index("ix_hr_attendance_corrections_attendance_record_id", table_name="hr_attendance_corrections")
    op.drop_index("ix_hr_attendance_corrections_company_id", table_name="hr_attendance_corrections")
    op.drop_table("hr_attendance_corrections")
    op.drop_index("ix_hr_attendance_company_date", table_name="hr_attendance_records")
    op.drop_index("ix_hr_attendance_records_employee_id", table_name="hr_attendance_records")
    op.drop_index("ix_hr_attendance_records_company_id", table_name="hr_attendance_records")
    op.drop_table("hr_attendance_records")
