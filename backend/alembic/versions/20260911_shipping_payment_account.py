"""add shipping payment account mapping

Revision ID: 20260911_shipping_payment_account
Revises: 20260911_salla_webhook_security
"""
from alembic import op
import sqlalchemy as sa

revision = "20260911_shipping_payment_account"
down_revision = "20260911_salla_webhook_security"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "shipping_methods",
        sa.Column("payment_account_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_shipping_method_payment_account",
        "shipping_methods",
        "account_combinations",
        ["payment_account_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index("ix_shipping_methods_payment_account_id", "shipping_methods", ["payment_account_id"])


def downgrade():
    op.drop_index("ix_shipping_methods_payment_account_id", table_name="shipping_methods")
    op.drop_constraint("fk_shipping_method_payment_account", "shipping_methods", type_="foreignkey")
    op.drop_column("shipping_methods", "payment_account_id")
