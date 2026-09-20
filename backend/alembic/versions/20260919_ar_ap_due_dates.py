"""add AR/AP due dates"""

from alembic import op
import sqlalchemy as sa

revision = "20260919_ar_ap_due_dates"
down_revision = "20260919_merge_reconciliation_recipe_heads"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("sales_documents", sa.Column("due_date", sa.Date(), nullable=True))
    op.add_column("purchase_documents", sa.Column("due_date", sa.Date(), nullable=True))
    op.create_index("ix_sales_documents_due_date", "sales_documents", ["due_date"])
    op.create_index("ix_purchase_documents_due_date", "purchase_documents", ["due_date"])

def downgrade() -> None:
    op.drop_index("ix_purchase_documents_due_date", table_name="purchase_documents")
    op.drop_index("ix_sales_documents_due_date", table_name="sales_documents")
    op.drop_column("purchase_documents", "due_date")
    op.drop_column("sales_documents", "due_date")
