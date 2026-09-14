"""Add GRNI clearing account for receipt-to-bill accounting.

Revision ID: 20260914_commerce_grni
Revises: 20260914_purchase_line_variants
"""
from alembic import op
import sqlalchemy as sa

revision = "20260914_commerce_grni"
down_revision = "20260914_purchase_line_variants"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "commerce_accounting_settings",
        sa.Column("grni_account_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_commerce_accounting_settings_grni_account",
        "commerce_accounting_settings",
        "account_combinations",
        ["grni_account_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    # Existing configurations are intentionally left nullable during migration.
    # New/updated configurations are required to provide GRNI through the API.


def downgrade():
    op.drop_constraint(
        "fk_commerce_accounting_settings_grni_account",
        "commerce_accounting_settings",
        type_="foreignkey",
    )
    op.drop_column("commerce_accounting_settings", "grni_account_id")
