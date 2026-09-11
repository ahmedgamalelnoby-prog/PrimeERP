"""enforce tenant-company business key uniqueness

Revision ID: 20260911_business_uniqueness
Revises: 20260911_shipping_settlement_guards
"""
from alembic import op

revision = "20260911_business_uniqueness"
down_revision = "20260911_shipping_settlement_guards"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "uq_tax_rate_company_code",
        "tax_rates",
        ["company_id", "code"],
        unique=True,
    )
    op.create_index(
        "uq_commerce_partner_company_code",
        "commerce_partners",
        ["company_id", "code"],
        unique=True,
    )
    op.create_index(
        "uq_sales_document_company_number",
        "sales_documents",
        ["company_id", "number"],
        unique=True,
    )
    op.create_index(
        "uq_purchase_document_company_number",
        "purchase_documents",
        ["company_id", "number"],
        unique=True,
    )
    op.create_index(
        "uq_shipping_carrier_company_code",
        "shipping_carriers",
        ["company_id", "code"],
        unique=True,
    )


def downgrade():
    op.drop_index("uq_shipping_carrier_company_code", table_name="shipping_carriers")
    op.drop_index("uq_purchase_document_company_number", table_name="purchase_documents")
    op.drop_index("uq_sales_document_company_number", table_name="sales_documents")
    op.drop_index("uq_commerce_partner_company_code", table_name="commerce_partners")
    op.drop_index("uq_tax_rate_company_code", table_name="tax_rates")
