"""make commerce payment idempotency keys unique per company

Revision ID: 20260912_commerce_idempotency
Revises: 20260912_accounting_rbac
"""

from alembic import op
import sqlalchemy as sa

revision = "20260912_commerce_idempotency"
down_revision = "20260912_accounting_rbac"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "uq_commerce_payments_company_idempotency_key",
        "commerce_payments",
        ["company_id", "idempotency_key"],
        unique=True,
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )


def downgrade():
    op.drop_index("uq_commerce_payments_company_idempotency_key", table_name="commerce_payments")
