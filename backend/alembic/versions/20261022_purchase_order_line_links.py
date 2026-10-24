"""Add purchase order references for goods receipts and supplier bills.

Revision ID: 20261022_purchase_order_line_links
Revises: 20261022_sales_order_line_links
"""
from alembic import op
import sqlalchemy as sa

revision = "20261022_purchase_order_line_links"
down_revision = "20261022_sales_order_line_links"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "purchase_documents",
        sa.Column("source_order_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_purchase_documents_source_order_id",
        "purchase_documents",
        "purchase_documents",
        ["source_order_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_purchase_documents_source_order_id",
        "purchase_documents",
        ["source_order_id"],
    )

    op.add_column(
        "purchase_lines",
        sa.Column("source_purchase_line_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_purchase_lines_source_purchase_line_id",
        "purchase_lines",
        "purchase_lines",
        ["source_purchase_line_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_purchase_lines_source_purchase_line_id",
        "purchase_lines",
        ["source_purchase_line_id"],
    )


def downgrade():
    op.drop_index("ix_purchase_lines_source_purchase_line_id", table_name="purchase_lines")
    op.drop_constraint(
        "fk_purchase_lines_source_purchase_line_id",
        "purchase_lines",
        type_="foreignkey",
    )
    op.drop_column("purchase_lines", "source_purchase_line_id")

    op.drop_index("ix_purchase_documents_source_order_id", table_name="purchase_documents")
    op.drop_constraint(
        "fk_purchase_documents_source_order_id",
        "purchase_documents",
        type_="foreignkey",
    )
    op.drop_column("purchase_documents", "source_order_id")
