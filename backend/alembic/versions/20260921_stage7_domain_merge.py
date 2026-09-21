"""merge Stage 6 treasury accounting and Stage 7 POS heads.

Revision ID: 20260921_stage7_domain_merge
Revises: 20260921_treasury_accounting_integration, 20260921_pos_domain
"""

revision = "20260921_stage7_domain_merge"
down_revision = (
    "20260921_treasury_accounting_integration",
    "20260921_pos_domain",
)
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
