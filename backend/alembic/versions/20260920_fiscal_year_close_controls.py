"""Fiscal year close control, checklist, privileged reopen and year-end audit."""
from alembic import op
import sqlalchemy as sa
revision="20260920_fiscal_year_close_controls"
# accounting_recognition_schedules already descends from enterprise_finance;
# listing both would create an invalid ancestor/descendant merge.
down_revision="20260920_accounting_recognition_schedules"
branch_labels=None
depends_on=None

def upgrade():
    op.create_table("fiscal_year_close_checklist_items",
        sa.Column("id",sa.Integer(),primary_key=True),
        sa.Column("tenant_id",sa.Integer(),sa.ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False),
        sa.Column("company_id",sa.Integer(),sa.ForeignKey("companies.id",ondelete="CASCADE"),nullable=False),
        sa.Column("fiscal_year_id",sa.Integer(),sa.ForeignKey("fiscal_years.id",ondelete="CASCADE"),nullable=False),
        sa.Column("key",sa.String(80),nullable=False),
        sa.Column("name",sa.String(200),nullable=False),
        sa.Column("required",sa.Boolean(),server_default=sa.true(),nullable=False),
        sa.Column("status",sa.String(20),server_default="pending",nullable=False),
        sa.Column("details",sa.Text()),
        sa.Column("checked_by",sa.Integer(),sa.ForeignKey("users.id",ondelete="SET NULL")),
        sa.Column("checked_at",sa.DateTime(timezone=True)),
        sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
        sa.UniqueConstraint("tenant_id","company_id","fiscal_year_id","key",name="uq_fy_close_checklist"))
    op.create_table("fiscal_year_close_runs",
        sa.Column("id",sa.Integer(),primary_key=True),
        sa.Column("tenant_id",sa.Integer(),sa.ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False),
        sa.Column("company_id",sa.Integer(),sa.ForeignKey("companies.id",ondelete="CASCADE"),nullable=False),
        sa.Column("fiscal_year_id",sa.Integer(),sa.ForeignKey("fiscal_years.id",ondelete="CASCADE"),nullable=False),
        sa.Column("status",sa.String(30),server_default="precheck",nullable=False),
        sa.Column("reason",sa.Text()),
        sa.Column("closing_entry_id",sa.Integer(),sa.ForeignKey("journal_entries.id",ondelete="SET NULL")),
        sa.Column("initiated_by",sa.Integer(),sa.ForeignKey("users.id",ondelete="SET NULL")),
        sa.Column("completed_by",sa.Integer(),sa.ForeignKey("users.id",ondelete="SET NULL")),
        sa.Column("initiated_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
        sa.Column("completed_at",sa.DateTime(timezone=True)),
        sa.UniqueConstraint("tenant_id","company_id","fiscal_year_id",name="uq_fy_close_run"))
    op.create_table("fiscal_year_close_audits",
        sa.Column("id",sa.Integer(),primary_key=True),
        sa.Column("tenant_id",sa.Integer(),sa.ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False),
        sa.Column("company_id",sa.Integer(),sa.ForeignKey("companies.id",ondelete="CASCADE"),nullable=False),
        sa.Column("fiscal_year_id",sa.Integer(),sa.ForeignKey("fiscal_years.id",ondelete="CASCADE"),nullable=False),
        sa.Column("period_id",sa.Integer(),sa.ForeignKey("accounting_periods.id",ondelete="SET NULL")),
        sa.Column("action",sa.String(50),nullable=False),
        sa.Column("from_status",sa.String(30)),
        sa.Column("to_status",sa.String(30)),
        sa.Column("reason",sa.Text()),
        sa.Column("actor_id",sa.Integer(),sa.ForeignKey("users.id",ondelete="SET NULL")),
        sa.Column("metadata_json",sa.Text()),
        sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False))

def downgrade():
    op.drop_table("fiscal_year_close_audits")
    op.drop_table("fiscal_year_close_runs")
    op.drop_table("fiscal_year_close_checklist_items")
