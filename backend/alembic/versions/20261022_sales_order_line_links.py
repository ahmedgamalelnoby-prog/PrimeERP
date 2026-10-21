"""Add sales order references for delivery and invoice quantity controls.

Revision ID: 20261022_sales_order_line_links
Revises: 20261020_company_policy_settings
"""
from alembic import op
import sqlalchemy as sa

revision = "20261022_sales_order_line_links"
down_revision = "20261020_company_policy_settings"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "sales_documents",
        sa.Column("source_order_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_sales_documents_source_order_id",
        "sales_documents",
        "sales_documents",
        ["source_order_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_sales_documents_source_order_id",
        "sales_documents",
        ["source_order_id"],
    )

    op.add_column(
        "sales_lines",
        sa.Column("source_sales_line_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_sales_lines_source_sales_line_id",
        "sales_lines",
        "sales_lines",
        ["source_sales_line_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_sales_lines_source_sales_line_id",
        "sales_lines",
        ["source_sales_line_id"],
    )


def downgrade():
    op.drop_index("ix_sales_lines_source_sales_line_id", table_name="sales_lines")
    op.drop_constraint(
        "fk_sales_lines_source_sales_line_id",
        "sales_lines",
        type_="foreignkey",
    )
    op.drop_column("sales_lines", "source_sales_line_id")

    op.drop_index("ix_sales_documents_source_order_id", table_name="sales_documents")
    op.drop_constraint(
        "fk_sales_documents_source_order_id",
        "sales_documents",
        type_="foreignkey",
    )
    op.drop_column("sales_documents", "source_order_id")
