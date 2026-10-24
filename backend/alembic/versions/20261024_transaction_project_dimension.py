"""Add the project dimension to generic business transactions.

Revision ID: 20261024_transaction_project_dimension
Revises: 20261023_commerce_approval_lifecycle
"""
from alembic import op
import sqlalchemy as sa

revision = "20261024_transaction_project_dimension"
down_revision = "20261023_commerce_approval_lifecycle"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "business_transactions",
        sa.Column("project_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_business_transactions_project_id",
        "business_transactions",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_business_transactions_project_id",
        "business_transactions",
        ["project_id"],
    )


def downgrade():
    op.drop_index("ix_business_transactions_project_id", table_name="business_transactions")
    op.drop_constraint(
        "fk_business_transactions_project_id",
        "business_transactions",
        type_="foreignkey",
    )
    op.drop_column("business_transactions", "project_id")
