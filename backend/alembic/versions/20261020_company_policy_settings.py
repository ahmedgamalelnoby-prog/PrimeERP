"""Company-scoped typed policy settings registry.
Revision ID: 20261020_company_policy_settings
Revises: 20260923_legal_tax_eta_identity
"""
from alembic import op
import sqlalchemy as sa

revision = "20261020_company_policy_settings"
down_revision = "20260923_legal_tax_eta_identity"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "company_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("setting_key", sa.String(length=120), nullable=False),
        sa.Column("value_json", sa.JSON(), nullable=False),
        sa.Column("updated_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("company_id", "setting_key", name="uq_company_settings_company_key"),
    )
    op.create_index("ix_company_settings_tenant_id", "company_settings", ["tenant_id"])
    op.create_index("ix_company_settings_company_id", "company_settings", ["company_id"])


def downgrade():
    op.drop_index("ix_company_settings_company_id", table_name="company_settings")
    op.drop_index("ix_company_settings_tenant_id", table_name="company_settings")
    op.drop_table("company_settings")
