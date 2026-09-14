"""Add purchase price variance account for receipt-to-bill differences.

Revision ID: 20260914_commerce_ppv
Revises: 20260914_commerce_grni
"""
from alembic import op
import sqlalchemy as sa

revision = "20260914_commerce_ppv"
down_revision = "20260914_commerce_grni"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "commerce_accounting_settings",
        sa.Column("purchase_price_variance_account_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_commerce_accounting_settings_ppv_account",
        "commerce_accounting_settings",
        "account_combinations",
        ["purchase_price_variance_account_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade():
    op.drop_constraint(
        "fk_commerce_accounting_settings_ppv_account",
        "commerce_accounting_settings",
        type_="foreignkey",
    )
    op.drop_column("commerce_accounting_settings", "purchase_price_variance_account_id")
