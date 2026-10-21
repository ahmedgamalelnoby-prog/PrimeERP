"""POS cashier shifts and cash reconciliation.

Revision ID: 20261029_pos_cashier_shifts
Revises: 20261028_hr_overtime_workflow
"""
from alembic import op
import sqlalchemy as sa


revision = "20261029_pos_cashier_shifts"
down_revision = "20261028_hr_overtime_workflow"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "pos_cashier_shifts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("branch_id", sa.Integer(), sa.ForeignKey("branches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("terminal_id", sa.Integer(), sa.ForeignKey("pos_terminals.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("opened_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("closed_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("opening_cash", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("expected_cash", sa.Numeric(18, 4), nullable=True),
        sa.Column("counted_cash", sa.Numeric(18, 4), nullable=True),
        sa.Column("variance", sa.Numeric(18, 4), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("opening_cash >= 0", name="ck_pos_cashier_shift_opening_cash"),
        sa.CheckConstraint("status IN ('open','closed')", name="ck_pos_cashier_shift_status"),
        sa.CheckConstraint(
            "(status = 'open' AND closed_at IS NULL AND expected_cash IS NULL AND counted_cash IS NULL AND variance IS NULL) OR "
            "(status = 'closed' AND closed_at IS NOT NULL AND expected_cash IS NOT NULL AND counted_cash IS NOT NULL AND variance IS NOT NULL)",
            name="ck_pos_cashier_shift_close_values",
        ),
    )
    op.create_index("ix_pos_cashier_shifts_company_id", "pos_cashier_shifts", ["company_id"])
    op.create_index("ix_pos_cashier_shifts_branch_id", "pos_cashier_shifts", ["branch_id"])
    op.create_index("ix_pos_cashier_shifts_terminal_id", "pos_cashier_shifts", ["terminal_id"])
    op.create_index(
        "uq_pos_cashier_shift_open_terminal",
        "pos_cashier_shifts",
        ["terminal_id"],
        unique=True,
        postgresql_where=sa.text("status = 'open'"),
    )
    op.add_column("sales_documents", sa.Column("pos_shift_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_sales_documents_pos_shift_id",
        "sales_documents",
        "pos_cashier_shifts",
        ["pos_shift_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index("ix_sales_documents_pos_shift_id", "sales_documents", ["pos_shift_id"])


def downgrade():
    op.drop_index("ix_sales_documents_pos_shift_id", table_name="sales_documents")
    op.drop_constraint("fk_sales_documents_pos_shift_id", "sales_documents", type_="foreignkey")
    op.drop_column("sales_documents", "pos_shift_id")
    op.drop_index("uq_pos_cashier_shift_open_terminal", table_name="pos_cashier_shifts")
    op.drop_index("ix_pos_cashier_shifts_terminal_id", table_name="pos_cashier_shifts")
    op.drop_index("ix_pos_cashier_shifts_branch_id", table_name="pos_cashier_shifts")
    op.drop_index("ix_pos_cashier_shifts_company_id", table_name="pos_cashier_shifts")
    op.drop_table("pos_cashier_shifts")
