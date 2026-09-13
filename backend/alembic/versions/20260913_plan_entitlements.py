"""add canonical plan entitlement columns

Revision ID: 20260913_plan_entitlements
Revises: 20260912_release_gate_heads_merge
"""

from alembic import op
import sqlalchemy as sa


revision = "20260913_plan_entitlements"
down_revision = "20260912_release_gate_heads_merge"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("plans", sa.Column("max_users", sa.Integer(), nullable=True))
    op.add_column("plans", sa.Column("max_companies", sa.Integer(), nullable=True))
    op.add_column("plans", sa.Column("max_branches", sa.Integer(), nullable=True))
    op.add_column("plans", sa.Column("max_products", sa.Integer(), nullable=True))
    op.add_column("plans", sa.Column("max_integrations", sa.Integer(), nullable=True))
    op.add_column("plans", sa.Column("storage_limit_mb", sa.Integer(), nullable=True))
    op.create_check_constraint("ck_plan_max_users", "plans", "max_users IS NULL OR max_users >= 1")
    op.create_check_constraint("ck_plan_max_companies", "plans", "max_companies IS NULL OR max_companies >= 1")
    op.create_check_constraint("ck_plan_max_branches", "plans", "max_branches IS NULL OR max_branches >= 1")
    op.create_check_constraint("ck_plan_max_products", "plans", "max_products IS NULL OR max_products >= 1")
    op.create_check_constraint("ck_plan_max_integrations", "plans", "max_integrations IS NULL OR max_integrations >= 0")
    op.create_check_constraint("ck_plan_storage_limit_mb", "plans", "storage_limit_mb IS NULL OR storage_limit_mb >= 1")


def downgrade():
    op.drop_constraint("ck_plan_storage_limit_mb", "plans", type_="check")
    op.drop_constraint("ck_plan_max_integrations", "plans", type_="check")
    op.drop_constraint("ck_plan_max_products", "plans", type_="check")
    op.drop_constraint("ck_plan_max_branches", "plans", type_="check")
    op.drop_constraint("ck_plan_max_companies", "plans", type_="check")
    op.drop_constraint("ck_plan_max_users", "plans", type_="check")
    op.drop_column("plans", "storage_limit_mb")
    op.drop_column("plans", "max_integrations")
    op.drop_column("plans", "max_products")
    op.drop_column("plans", "max_branches")
    op.drop_column("plans", "max_companies")
    op.drop_column("plans", "max_users")
