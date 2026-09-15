"""Harden commerce payment reversal integrity.

Revision ID: 20260915_commerce_payment_integrity
Revises: 20260915_commerce_accounting_integrity
"""
from alembic import op
import sqlalchemy as sa

revision = "20260915_commerce_payment_integrity"
down_revision = "20260915_commerce_accounting_integrity"
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint(
        "uq_commerce_payments_company_id",
        "commerce_payments",
        ["company_id", "id"],
    )
    op.create_foreign_key(
        "fk_commerce_payment_reversal_same_company",
        "commerce_payments",
        "commerce_payments",
        ["company_id", "reversed_of_id"],
        ["company_id", "id"],
        ondelete="RESTRICT",
    )
    op.create_check_constraint(
        "ck_commerce_payment_reversal_state",
        "commerce_payments",
        "(status = 'posted' AND reversed_at IS NULL) OR (status = 'reversed' AND reversed_at IS NOT NULL)",
    )


def downgrade():
    op.drop_constraint("ck_commerce_payment_reversal_state", "commerce_payments", type_="check")
    op.drop_constraint("fk_commerce_payment_reversal_same_company", "commerce_payments", type_="foreignkey")
    op.drop_constraint("uq_commerce_payments_company_id", "commerce_payments", type_="unique")
