from alembic import op
import sqlalchemy as sa

revision="20260921_rentals_collections_renewals"
down_revision="20260921_rentals_module_catalog"
branch_labels=None
depends_on=None

def upgrade():
    op.add_column("rental_charges", sa.Column("due_date", sa.Date(), nullable=True))
    op.create_table("rental_receipts",
        sa.Column("id",sa.Integer(),primary_key=True),
        sa.Column("tenant_id",sa.Integer(),sa.ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False),
        sa.Column("company_id",sa.Integer(),sa.ForeignKey("companies.id",ondelete="CASCADE"),nullable=False),
        sa.Column("charge_id",sa.Integer(),sa.ForeignKey("rental_charges.id",ondelete="RESTRICT"),nullable=False),
        sa.Column("payment_date",sa.Date(),nullable=False),
        sa.Column("amount",sa.Numeric(18,4),nullable=False),
        sa.Column("method",sa.String(30),nullable=False),
        sa.Column("reference",sa.String(120)),
        sa.Column("status",sa.String(20),nullable=False,server_default="pending"),
        sa.Column("journal_entry_id",sa.Integer(),sa.ForeignKey("journal_entries.id",ondelete="SET NULL")),
        sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
        sa.CheckConstraint("amount > 0",name="ck_rental_receipt_amount"),
        sa.CheckConstraint("status IN ('pending','posted','reversed')",name="ck_rental_receipt_status"))
    op.create_index("ix_rental_receipts_tenant_id","rental_receipts",["tenant_id"])
    op.create_index("ix_rental_receipts_company_id","rental_receipts",["company_id"])
    op.create_index("ix_rental_receipts_charge_id","rental_receipts",["charge_id"])
    op.create_index("ix_rental_receipts_journal_entry_id","rental_receipts",["journal_entry_id"])

def downgrade():
    op.drop_table("rental_receipts")
    op.drop_column("rental_charges","due_date")
