"""CRM leads and HR employment contracts
Revision ID: 20260920_crm_hr_completion
"""
from alembic import op
import sqlalchemy as sa
revision="20260920_crm_hr_completion"
down_revision="20260920_mrp_planning_completion"
branch_labels=None
depends_on=None
def upgrade():
    op.create_table("crm_leads",
        sa.Column("id",sa.Integer(),primary_key=True),
        sa.Column("company_id",sa.Integer(),sa.ForeignKey("companies.id",ondelete="CASCADE"),nullable=False),
        sa.Column("name",sa.String(200),nullable=False),sa.Column("phone",sa.String(80)),
        sa.Column("email",sa.String(200)),sa.Column("source",sa.String(80)),
        sa.Column("status",sa.String(30),nullable=False,server_default="new"),
        sa.Column("owner_id",sa.Integer(),sa.ForeignKey("users.id",ondelete="SET NULL")),
        sa.Column("notes",sa.Text()),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now()))
    op.create_index("ix_crm_leads_company_id","crm_leads",["company_id"])
    op.create_table("hr_employment_contracts",
        sa.Column("id",sa.Integer(),primary_key=True),
        sa.Column("company_id",sa.Integer(),sa.ForeignKey("companies.id",ondelete="CASCADE"),nullable=False),
        sa.Column("employee_id",sa.Integer(),sa.ForeignKey("employees.id",ondelete="CASCADE"),nullable=False),
        sa.Column("start_date",sa.Date(),nullable=False),sa.Column("end_date",sa.Date()),
        sa.Column("salary",sa.Numeric(18,4),nullable=False,server_default="0"),
        sa.Column("status",sa.String(30),nullable=False,server_default="active"),sa.Column("notes",sa.Text()))
    op.create_index("ix_hr_employment_contracts_company_id","hr_employment_contracts",["company_id"])
    op.create_index("ix_hr_employment_contracts_employee_id","hr_employment_contracts",["employee_id"])
    op.create_unique_constraint("uq_hr_contract_employee_start","hr_employment_contracts",["employee_id","start_date"])
def downgrade():
    op.drop_constraint("uq_hr_contract_employee_start","hr_employment_contracts",type_="unique")
    op.drop_index("ix_hr_employment_contracts_employee_id",table_name="hr_employment_contracts")
    op.drop_index("ix_hr_employment_contracts_company_id",table_name="hr_employment_contracts")
    op.drop_table("hr_employment_contracts")
    op.drop_index("ix_crm_leads_company_id",table_name="crm_leads")
    op.drop_table("crm_leads")
