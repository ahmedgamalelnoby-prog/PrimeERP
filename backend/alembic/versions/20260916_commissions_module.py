"""Create commission rules and settlements.

Revision ID: 20260916_commissions_module
Revises: 20260916_enterprise_module_integrity
"""
from alembic import op
import sqlalchemy as sa

revision = "20260916_commissions_module"
down_revision = "20260916_enterprise_module_integrity"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "commission_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(60), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("basis", sa.String(30), nullable=False, server_default="net_sales"),
        sa.Column("rate_percent", sa.Numeric(8, 4), nullable=False, server_default="0"),
        sa.Column("fixed_amount", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("min_base", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("max_base", sa.Numeric(18, 4)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("company_id", "code", name="uq_commission_rule_company_code"),
        sa.CheckConstraint("basis IN ('gross_sales','net_sales','gross_profit','collection')", name="ck_commission_rule_basis"),
        sa.CheckConstraint("rate_percent >= 0 AND rate_percent <= 100", name="ck_commission_rule_rate"),
        sa.CheckConstraint("fixed_amount >= 0 AND min_base >= 0", name="ck_commission_rule_nonnegative"),
        sa.CheckConstraint("max_base IS NULL OR max_base >= min_base", name="ck_commission_rule_base_range"),
    )
    op.create_index("ix_commission_rules_company", "commission_rules", ["company_id"])

    op.create_table(
        "commission_settlements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("rule_id", sa.Integer(), sa.ForeignKey("commission_rules.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("period", sa.String(7), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("source_id", sa.Integer()),
        sa.Column("base_amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("commission_amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("base_amount >= 0 AND commission_amount >= 0", name="ck_commission_settlement_amounts"),
        sa.CheckConstraint("status IN ('draft','approved','posted','cancelled')", name="ck_commission_settlement_status"),
        sa.CheckConstraint("length(period) = 7 AND substr(period,5,1) = '-'", name="ck_commission_settlement_period"),
        sa.UniqueConstraint("company_id", "employee_id", "rule_id", "period", "source_type", "source_id", name="uq_commission_settlement_source"),
    )
    op.create_index("ix_commission_settlements_company", "commission_settlements", ["company_id"])
    op.create_index("ix_commission_settlements_employee", "commission_settlements", ["employee_id"])
    op.create_index("ix_commission_settlements_rule", "commission_settlements", ["rule_id"])


def downgrade():
    op.drop_index("ix_commission_settlements_rule", table_name="commission_settlements")
    op.drop_index("ix_commission_settlements_employee", table_name="commission_settlements")
    op.drop_index("ix_commission_settlements_company", table_name="commission_settlements")
    op.drop_table("commission_settlements")
    op.drop_index("ix_commission_rules_company", table_name="commission_rules")
    op.drop_table("commission_rules")
