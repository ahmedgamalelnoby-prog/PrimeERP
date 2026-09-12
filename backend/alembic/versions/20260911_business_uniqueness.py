"""enforce tenant-company business key uniqueness

Revision ID: 20260911_business_uniqueness
Revises: 20260911_shipping_settlement_guards

The canonical commerce schema may already create some of these indexes. This
migration therefore uses PostgreSQL's idempotent CREATE UNIQUE INDEX form so a
fresh database can traverse the complete migration graph without attempting to
recreate an existing relation.
"""
from alembic import op

revision = "20260911_business_uniqueness"
down_revision = "20260911_shipping_settlement_guards"
branch_labels = None
depends_on = None


_UNIQUE_INDEXES = (
    ("uq_tax_rate_company_code", "tax_rates", "company_id, code"),
    ("uq_commerce_partner_company_code", "commerce_partners", "company_id, code"),
    ("uq_sales_document_company_number", "sales_documents", "company_id, number"),
    ("uq_purchase_document_company_number", "purchase_documents", "company_id, number"),
    ("uq_shipping_carrier_company_code", "shipping_carriers", "company_id, code"),
)


def upgrade():
    for index_name, table_name, columns in _UNIQUE_INDEXES:
        op.execute(
            f"CREATE UNIQUE INDEX IF NOT EXISTS {index_name} "
            f"ON {table_name} ({columns})"
        )


def downgrade():
    # These indexes can be owned by the canonical schema on branches where
    # they predate this compatibility migration. Do not remove them here.
    pass
