"""enforce tax rate percentage bounds

Revision ID: 20260911_tax_rate_bounds
Revises: 20260911_commerce_wht
"""
from alembic import op

revision = "20260911_tax_rate_bounds"
down_revision = "20260911_commerce_wht"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("ck_tax_rate_nonnegative", "tax_rates", type_="check")
    op.create_check_constraint("ck_tax_rate_bounds", "tax_rates", "rate >= 0 AND rate <= 100")


def downgrade():
    op.drop_constraint("ck_tax_rate_bounds", "tax_rates", type_="check")
    op.create_check_constraint("ck_tax_rate_nonnegative", "tax_rates", "rate >= 0")
