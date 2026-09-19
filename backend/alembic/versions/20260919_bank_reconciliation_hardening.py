"""harden bank reconciliation source uniqueness

Revision ID: 20260919_bank_reconciliation_hardening
Revises: 20260919_bank_reconciliation
"""
from alembic import op

revision = "20260919_bank_reconciliation_hardening"
down_revision = "20260919_bank_reconciliation"
branch_labels = None
depends_on = None

def upgrade():
    op.drop_constraint("uq_treasury_reconciliation_match_source", "treasury_reconciliation_matches", type_="unique")
    op.create_unique_constraint(
        "uq_treasury_reconciliation_match_session_source",
        "treasury_reconciliation_matches",
        ["session_id", "source_type", "source_id"],
    )

def downgrade():
    op.drop_constraint("uq_treasury_reconciliation_match_session_source", "treasury_reconciliation_matches", type_="unique")
    op.create_unique_constraint(
        "uq_treasury_reconciliation_match_source",
        "treasury_reconciliation_matches",
        ["statement_line_id", "source_type", "source_id"],
    )
