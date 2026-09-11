"""add idempotency key for commerce payments

Revision ID: 20260911_commerce_payment_idempotency
Revises: 20260911_business_uniqueness
"""
from alembic import op
import sqlalchemy as sa

revision = "20260911_commerce_payment_idempotency"
down_revision = "20260911_business_uniqueness"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("commerce_payments", sa.Column("idempotency_key", sa.String(length=100), nullable=True))
    op.create_index("ix_commerce_payments_idempotency_key", "commerce_payments", ["idempotency_key"])
    op.create_index(
        "uq_commerce_payment_company_idempotency",
        "commerce_payments",
        ["company_id", "idempotency_key"],
        unique=True,
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )


def downgrade():
    op.drop_index("uq_commerce_payment_company_idempotency", table_name="commerce_payments")
    op.drop_index("ix_commerce_payments_idempotency_key", table_name="commerce_payments")
    op.drop_column("commerce_payments", "idempotency_key")
