"""Link payroll runs to accounting journals.
Revision ID: 20260920_payroll_journal_link
Revises: 20260920_purchase_return_completion
"""
from alembic import op
import sqlalchemy as sa
revision="20260920_payroll_journal_link"
down_revision="20260920_purchase_return_completion"
branch_labels=None
depends_on=None
def upgrade():
    op.add_column("payroll_runs", sa.Column("journal_entry_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_payroll_runs_journal_entry_id","payroll_runs","journal_entries",["journal_entry_id"],["id"],ondelete="SET NULL")
    op.create_index("ix_payroll_runs_journal_entry_id","payroll_runs",["journal_entry_id"])
def downgrade():
    op.drop_index("ix_payroll_runs_journal_entry_id",table_name="payroll_runs")
    op.drop_constraint("fk_payroll_runs_journal_entry_id","payroll_runs",type_="foreignkey")
    op.drop_column("payroll_runs","journal_entry_id")
