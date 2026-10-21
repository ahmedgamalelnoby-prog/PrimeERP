"""sales invoice document and accounting posting bridge
Revision ID: 20260921_sales_invoice
Revises: 20260921_sales_fulfillment
"""
from alembic import op
import sqlalchemy as sa
revision="20260921_sales_invoice"
down_revision="20260921_sales_fulfillment"
branch_labels=None
depends_on=None
def upgrade():
 op.create_table("sales_invoice_lines",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("invoice_id",sa.Integer(),nullable=False),sa.Column("product_id",sa.Integer(),nullable=False),sa.Column("quantity",sa.Numeric(18,6),nullable=False),sa.Column("unit_price",sa.Numeric(18,2),nullable=False),sa.Column("discount",sa.Numeric(18,2),nullable=False,server_default="0"),sa.Column("tax_rate",sa.Numeric(9,4),nullable=False,server_default="0"),sa.Column("line_total",sa.Numeric(18,2),nullable=False),sa.ForeignKeyConstraint(["invoice_id"],["sales_invoices.id"],ondelete="CASCADE"),sa.ForeignKeyConstraint(["product_id"],["products.id"],ondelete="RESTRICT"))
 op.create_index("ix_sales_invoice_lines_invoice","sales_invoice_lines",["invoice_id"])
 op.add_column("sales_invoices",sa.Column("journal_entry_id",sa.Integer(),nullable=True))
 op.create_foreign_key("fk_sales_invoice_journal","sales_invoices","journal_entries",["journal_entry_id"],["id"],ondelete="SET NULL")
 op.create_index("ix_sales_invoices_journal","sales_invoices",["journal_entry_id"])
def downgrade():
 op.drop_index("ix_sales_invoices_journal",table_name="sales_invoices");op.drop_constraint("fk_sales_invoice_journal","sales_invoices",type_="foreignkey");op.drop_column("sales_invoices","journal_entry_id");op.drop_index("ix_sales_invoice_lines_invoice",table_name="sales_invoice_lines");op.drop_table("sales_invoice_lines")
