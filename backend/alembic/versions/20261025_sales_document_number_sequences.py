"""Add transaction-safe sales document numbering sequences.

Revision ID: 20261025_sales_document_number_sequences
Revises: 20261024_transaction_project_dimension
"""
from alembic import op
import sqlalchemy as sa

revision = "20261025_sales_document_number_sequences"
down_revision = "20261024_transaction_project_dimension"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "commerce_document_number_sequences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("scope_key", sa.String(length=180), nullable=False),
        sa.Column("current_value", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("scope_key", name="uq_commerce_document_sequence_scope"),
        sa.CheckConstraint("current_value >= 0", name="ck_commerce_document_sequence_value"),
    )


def downgrade():
    op.drop_table("commerce_document_number_sequences")
