"""Add employee leave balances and approval lifecycle."""
from alembic import op
import sqlalchemy as sa

revision = "20261026_hr_leave_workflow"
down_revision = "20261025_sales_document_number_sequences"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "hr_leave_balances",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("leave_type", sa.String(length=20), nullable=False),
        sa.Column("entitled_days", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("consumed_days", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("company_id", "employee_id", "leave_type", name="uq_hr_leave_balance_employee_type"),
        sa.CheckConstraint("leave_type IN ('annual','sick','other')", name="ck_hr_leave_balance_type"),
        sa.CheckConstraint("entitled_days >= 0 AND consumed_days >= 0", name="ck_hr_leave_balance_values"),
    )
    op.create_index("ix_hr_leave_balances_company_id", "hr_leave_balances", ["company_id"])
    op.create_index("ix_hr_leave_balances_employee_id", "hr_leave_balances", ["employee_id"])

    op.create_table(
        "hr_leave_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("leave_type", sa.String(length=20), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("requested_days", sa.Numeric(10, 2), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("submitted_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("decided_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("leave_type IN ('annual','sick','unpaid','other')", name="ck_hr_leave_request_type"),
        sa.CheckConstraint("status IN ('pending','approved','rejected','cancelled')", name="ck_hr_leave_request_status"),
        sa.CheckConstraint("end_date >= start_date", name="ck_hr_leave_request_dates"),
        sa.CheckConstraint("requested_days > 0", name="ck_hr_leave_request_days"),
    )
    op.create_index("ix_hr_leave_requests_company_id", "hr_leave_requests", ["company_id"])
    op.create_index("ix_hr_leave_requests_employee_id", "hr_leave_requests", ["employee_id"])
    op.create_index(
        "ix_hr_leave_request_overlap",
        "hr_leave_requests",
        ["company_id", "employee_id", "start_date", "end_date", "status"],
    )


def downgrade():
    op.drop_index("ix_hr_leave_request_overlap", table_name="hr_leave_requests")
    op.drop_index("ix_hr_leave_requests_employee_id", table_name="hr_leave_requests")
    op.drop_index("ix_hr_leave_requests_company_id", table_name="hr_leave_requests")
    op.drop_table("hr_leave_requests")
    op.drop_index("ix_hr_leave_balances_employee_id", table_name="hr_leave_balances")
    op.drop_index("ix_hr_leave_balances_company_id", table_name="hr_leave_balances")
    op.drop_table("hr_leave_balances")
