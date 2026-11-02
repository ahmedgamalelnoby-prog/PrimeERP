"""Harden POS invoice replay identity at the database boundary."""
from alembic import op
import sqlalchemy as sa

revision = "20260922_pos_invoice_replay_guard"
down_revision = "20260920_enterprise_finance"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_index(
        "uq_sales_documents_company_invoice_number",
        "sales_documents",
        ["company_id", "number"],
        unique=True,
        postgresql_where=sa.text("document_type = 'invoice'"),
    )

def downgrade() -> None:
    op.drop_index("uq_sales_documents_company_invoice_number", table_name="sales_documents")
