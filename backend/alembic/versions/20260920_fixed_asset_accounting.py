"""Fixed asset accounting mappings and auditable depreciation runs."""
from alembic import op
import sqlalchemy as sa

revision = "20260920_fixed_asset_accounting"
down_revision = "20260920_enterprise_business_key_guards"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("fixed_assets", sa.Column("asset_account_id", sa.Integer(), nullable=True))
    op.add_column("fixed_assets", sa.Column("accumulated_depreciation_account_id", sa.Integer(), nullable=True))
    op.add_column("fixed_assets", sa.Column("depreciation_expense_account_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_fixed_assets_asset_account", "fixed_assets", "account_combinations", ["asset_account_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_fixed_assets_accum_depr_account", "fixed_assets", "account_combinations", ["accumulated_depreciation_account_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_fixed_assets_depr_expense_account", "fixed_assets", "account_combinations", ["depreciation_expense_account_id"], ["id"], ondelete="RESTRICT")
    op.create_index("ix_fixed_assets_asset_account_id", "fixed_assets", ["asset_account_id"])
    op.create_index("ix_fixed_assets_accumulated_depreciation_account_id", "fixed_assets", ["accumulated_depreciation_account_id"])
    op.create_index("ix_fixed_assets_depreciation_expense_account_id", "fixed_assets", ["depreciation_expense_account_id"])

    op.create_table(
        "fixed_asset_depreciation_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("asset_id", sa.Integer(), sa.ForeignKey("fixed_assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("posting_date", sa.Date(), nullable=False),
        sa.Column("months", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("journal_entry_id", sa.Integer(), sa.ForeignKey("journal_entries.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("asset_id", "posting_date", name="uq_fixed_asset_depr_asset_date"),
        sa.CheckConstraint("months > 0", name="ck_fixed_asset_depr_months"),
        sa.CheckConstraint("amount >= 0", name="ck_fixed_asset_depr_amount"),
        sa.CheckConstraint("status IN ('pending','posted','cancelled')", name="ck_fixed_asset_depr_status"),
    )
    op.create_index("ix_fixed_asset_depreciation_runs_tenant_company", "fixed_asset_depreciation_runs", ["tenant_id", "company_id"])
    op.create_index("ix_fixed_asset_depreciation_runs_asset_id", "fixed_asset_depreciation_runs", ["asset_id"])
    op.create_index("ix_fixed_asset_depreciation_runs_journal_entry_id", "fixed_asset_depreciation_runs", ["journal_entry_id"])


def downgrade():
    op.drop_index("ix_fixed_asset_depreciation_runs_journal_entry_id", table_name="fixed_asset_depreciation_runs")
    op.drop_index("ix_fixed_asset_depreciation_runs_asset_id", table_name="fixed_asset_depreciation_runs")
    op.drop_index("ix_fixed_asset_depreciation_runs_tenant_company", table_name="fixed_asset_depreciation_runs")
    op.drop_table("fixed_asset_depreciation_runs")
    op.drop_index("ix_fixed_assets_depreciation_expense_account_id", table_name="fixed_assets")
    op.drop_index("ix_fixed_assets_accumulated_depreciation_account_id", table_name="fixed_assets")
    op.drop_index("ix_fixed_assets_asset_account_id", table_name="fixed_assets")
    op.drop_constraint("fk_fixed_assets_depr_expense_account", "fixed_assets", type_="foreignkey")
    op.drop_constraint("fk_fixed_assets_accum_depr_account", "fixed_assets", type_="foreignkey")
    op.drop_constraint("fk_fixed_assets_asset_account", "fixed_assets", type_="foreignkey")
    op.drop_column("fixed_assets", "depreciation_expense_account_id")
    op.drop_column("fixed_assets", "accumulated_depreciation_account_id")
    op.drop_column("fixed_assets", "asset_account_id")
