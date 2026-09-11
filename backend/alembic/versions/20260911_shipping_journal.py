"""configure shipping settlement journal and branch

Revision ID: 20260911_shipping_journal
Revises: 20260911_shipping_accounting
"""
from alembic import op
import sqlalchemy as sa

revision = "20260911_shipping_journal"
down_revision = "20260911_shipping_accounting"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("shipping_carriers", sa.Column("settlement_journal_id", sa.Integer(), nullable=True))
    op.add_column("shipping_carriers", sa.Column("branch_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_shipping_carrier_settlement_journal", "shipping_carriers", "accounting_journals", ["settlement_journal_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_shipping_carrier_branch", "shipping_carriers", "branches", ["branch_id"], ["id"], ondelete="RESTRICT")
    op.create_index("ix_shipping_carrier_settlement_journal", "shipping_carriers", ["settlement_journal_id"])
    op.create_index("ix_shipping_carrier_branch", "shipping_carriers", ["branch_id"])


def downgrade():
    op.drop_index("ix_shipping_carrier_branch", table_name="shipping_carriers")
    op.drop_index("ix_shipping_carrier_settlement_journal", table_name="shipping_carriers")
    op.drop_constraint("fk_shipping_carrier_branch", "shipping_carriers", type_="foreignkey")
    op.drop_constraint("fk_shipping_carrier_settlement_journal", "shipping_carriers", type_="foreignkey")
    op.drop_column("shipping_carriers", "branch_id")
    op.drop_column("shipping_carriers", "settlement_journal_id")
