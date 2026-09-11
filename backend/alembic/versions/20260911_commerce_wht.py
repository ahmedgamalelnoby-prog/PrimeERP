"""add withholding tax amounts to commerce payments"""
from alembic import op
import sqlalchemy as sa

revision = "20260911_commerce_wht"
down_revision = "20260911_product_merge"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("commerce_payments", sa.Column("wht_amount", sa.Numeric(18, 4), nullable=False, server_default="0"))
    op.create_check_constraint("ck_commerce_payment_wht", "commerce_payments", "wht_amount >= 0 AND wht_amount <= amount")


def downgrade():
    op.drop_constraint("ck_commerce_payment_wht", "commerce_payments", type_="check")
    op.drop_column("commerce_payments", "wht_amount")
