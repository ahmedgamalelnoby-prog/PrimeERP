"""Add ERP source linkage to shipments.

Revision ID: 20260911shipbridge
Revises: 20260911shipping
"""
from alembic import op
import sqlalchemy as sa

revision = "20260911shipbridge"
down_revision = "20260911shipping"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("shipments", sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=True))
    op.add_column("shipments", sa.Column("branch_id", sa.Integer(), sa.ForeignKey("branches.id", ondelete="RESTRICT"), nullable=True))
    op.add_column("shipments", sa.Column("transaction_id", sa.Integer(), sa.ForeignKey("business_transactions.id", ondelete="SET NULL"), nullable=True))
    op.add_column("shipments", sa.Column("source_module", sa.String(80), nullable=True))
    op.add_column("shipments", sa.Column("source_entity", sa.String(100), nullable=True))
    op.add_column("shipments", sa.Column("source_id", sa.Integer(), nullable=True))
    op.create_index("ix_shipments_company_id", "shipments", ["company_id"])
    op.create_index("ix_shipments_branch_id", "shipments", ["branch_id"])
    op.create_index("ix_shipments_transaction_id", "shipments", ["transaction_id"])
    op.create_index("ix_shipments_source_lookup", "shipments", ["tenant_id", "source_module", "source_entity", "source_id"])


def downgrade():
    op.drop_index("ix_shipments_source_lookup", table_name="shipments")
    op.drop_index("ix_shipments_transaction_id", table_name="shipments")
    op.drop_index("ix_shipments_branch_id", table_name="shipments")
    op.drop_index("ix_shipments_company_id", table_name="shipments")
    op.drop_column("shipments", "source_id")
    op.drop_column("shipments", "source_entity")
    op.drop_column("shipments", "source_module")
    op.drop_column("shipments", "transaction_id")
    op.drop_column("shipments", "branch_id")
    op.drop_column("shipments", "company_id")
