"""Link POS sales invoices to cashier sessions for reconciliation."""
from alembic import op
import sqlalchemy as sa

revision = "20260920_pos_session_sales_link"
down_revision = "20260920_fixed_asset_accounting"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("sales_documents", sa.Column("pos_session_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_sales_documents_pos_session", "sales_documents", "pos_sessions", ["pos_session_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_sales_documents_pos_session_id", "sales_documents", ["pos_session_id"])


def downgrade():
    op.drop_index("ix_sales_documents_pos_session_id", table_name="sales_documents")
    op.drop_constraint("fk_sales_documents_pos_session", "sales_documents", type_="foreignkey")
    op.drop_column("sales_documents", "pos_session_id")
