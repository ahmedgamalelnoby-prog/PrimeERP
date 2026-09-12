"""enforce unique commerce document numbers per company/type

Revision ID: 20260912_document_number_constraints
Revises: 20260912_uom_constraints
"""

from alembic import op

revision = "20260912_document_number_constraints"
down_revision = "20260912_uom_constraints"
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint(
        "uq_sales_documents_company_type_number",
        "sales_documents",
        ["company_id", "document_type", "number"],
    )
    op.create_unique_constraint(
        "uq_purchase_documents_company_type_number",
        "purchase_documents",
        ["company_id", "document_type", "number"],
    )


def downgrade():
    op.drop_constraint("uq_purchase_documents_company_type_number", "purchase_documents", type_="unique")
    op.drop_constraint("uq_sales_documents_company_type_number", "sales_documents", type_="unique")
