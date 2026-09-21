"""Treasury accounting linkage and cheque lifecycle."""
from alembic import op
import sqlalchemy as sa
revision="20260921_treasury_accounting"
down_revision="20260921_shipping_foundation"
branch_labels=None
depends_on=None
def upgrade():
    op.add_column("treasury_accounts",sa.Column("accounting_account_combination_id",sa.Integer(),sa.ForeignKey("account_combinations.id",ondelete="RESTRICT"),nullable=True))
    op.create_index("ix_treasury_accounts_gl_account","treasury_accounts",["tenant_id","accounting_account_combination_id"])
def downgrade():
    op.drop_index("ix_treasury_accounts_gl_account",table_name="treasury_accounts")
    op.drop_column("treasury_accounts","accounting_account_combination_id")
