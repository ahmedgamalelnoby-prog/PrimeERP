"""Add industry-aware company profile for shared ERP business rules.

Revision ID: 20260919_industry_profile
Revises: 20260919_product_item_semantics
"""
from alembic import op
import sqlalchemy as sa

revision = "20260919_industry_profile"
down_revision = "20260919_product_item_semantics"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "company_industry_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("industry_code", sa.String(50), nullable=False),
        sa.Column("business_model", sa.String(50), nullable=False, server_default="hybrid"),
        sa.Column("configuration_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("company_id", name="uq_company_industry_profile_company"),
    )
    op.create_index("ix_company_industry_profiles_company_id", "company_industry_profiles", ["company_id"])
    op.create_index("ix_company_industry_profiles_industry_code", "company_industry_profiles", ["industry_code"])


def downgrade() -> None:
    op.drop_index("ix_company_industry_profiles_industry_code", table_name="company_industry_profiles")
    op.drop_index("ix_company_industry_profiles_company_id", table_name="company_industry_profiles")
    op.drop_table("company_industry_profiles")
