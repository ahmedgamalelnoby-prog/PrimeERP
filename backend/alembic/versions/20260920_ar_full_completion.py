from alembic import op
import sqlalchemy as sa

revision="20260920_ar_full_completion"
down_revision="20260920_fiscal_year_close_controls"
branch_labels=None
depends_on=None

def upgrade():
    op.add_column("commerce_payments", sa.Column("partner_id", sa.Integer(), sa.ForeignKey("commerce_partners.id", ondelete="RESTRICT"), nullable=True))
    op.alter_column("commerce_payments", "document_id", existing_type=sa.Integer(), nullable=True)
    op.create_index("ix_commerce_payments_partner_id", "commerce_payments", ["partner_id"])
    op.create_table("ar_write_offs",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("company_id",sa.Integer(),sa.ForeignKey("companies.id",ondelete="CASCADE"),nullable=False),sa.Column("partner_id",sa.Integer(),sa.ForeignKey("commerce_partners.id",ondelete="RESTRICT"),nullable=False),sa.Column("document_id",sa.Integer(),sa.ForeignKey("sales_documents.id",ondelete="RESTRICT"),nullable=False),sa.Column("amount",sa.Numeric(18,4),nullable=False),sa.Column("reason",sa.Text(),nullable=False),sa.Column("writeoff_account_id",sa.Integer(),sa.ForeignKey("account_combinations.id",ondelete="RESTRICT"),nullable=False),sa.Column("journal_id",sa.Integer(),sa.ForeignKey("accounting_journals.id",ondelete="RESTRICT"),nullable=False),sa.Column("status",sa.String(20),nullable=False,server_default="pending"),sa.Column("requested_by",sa.Integer(),sa.ForeignKey("users.id",ondelete="SET NULL")),sa.Column("approved_by",sa.Integer(),sa.ForeignKey("users.id",ondelete="SET NULL")),sa.Column("rejected_by",sa.Integer(),sa.ForeignKey("users.id",ondelete="SET NULL")),sa.Column("approved_at",sa.DateTime(timezone=True)),sa.Column("rejected_at",sa.DateTime(timezone=True)),sa.Column("accounting_entry_id",sa.Integer(),sa.ForeignKey("journal_entries.id",ondelete="SET NULL")),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),sa.CheckConstraint("amount > 0",name="ck_ar_writeoff_amount"),sa.CheckConstraint("status IN ('pending','approved','rejected')",name="ck_ar_writeoff_status"))
    op.create_index("ix_ar_write_offs_company_id","ar_write_offs",["company_id"])
    op.create_index("ix_ar_write_offs_partner_id","ar_write_offs",["partner_id"])
    op.create_index("ix_ar_write_offs_document_id","ar_write_offs",["document_id"])
    op.create_table("ar_reconciliations",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("company_id",sa.Integer(),sa.ForeignKey("companies.id",ondelete="CASCADE"),nullable=False),sa.Column("partner_id",sa.Integer(),sa.ForeignKey("commerce_partners.id",ondelete="RESTRICT")),sa.Column("as_of",sa.Date(),nullable=False),sa.Column("status",sa.String(20),nullable=False,server_default="balanced"),sa.Column("discrepancy_amount",sa.Numeric(18,4),nullable=False,server_default="0"),sa.Column("details_json",sa.Text(),nullable=False,server_default="{}"),sa.Column("reconciled_by",sa.Integer(),sa.ForeignKey("users.id",ondelete="SET NULL")),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False))
    op.create_index("ix_ar_reconciliations_company_id","ar_reconciliations",["company_id"])
    op.create_index("ix_ar_reconciliations_partner_id","ar_reconciliations",["partner_id"])

def downgrade():
    op.drop_table("ar_reconciliations");op.drop_table("ar_write_offs")
    op.drop_index("ix_commerce_payments_partner_id", table_name="commerce_payments")
    op.alter_column("commerce_payments", "document_id", existing_type=sa.Integer(), nullable=False)
    op.drop_column("commerce_payments", "partner_id")
