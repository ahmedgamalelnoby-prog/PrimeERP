"""merge inventory heads and add end-to-end sales purchasing lifecycle"""
from alembic import op
import sqlalchemy as sa

revision='20260911commerce'
down_revision=('20260911adjustments','20260911reservations')
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('commerce_partners',
        sa.Column('id',sa.Integer(),primary_key=True), sa.Column('company_id',sa.Integer(),nullable=False),
        sa.Column('code',sa.String(50),nullable=False), sa.Column('name',sa.String(200),nullable=False),
        sa.Column('partner_type',sa.String(20),nullable=False,server_default='customer'), sa.Column('tax_number',sa.String(50)),
        sa.Column('phone',sa.String(50)), sa.Column('email',sa.String(200)), sa.Column('credit_limit',sa.Numeric(18,4),server_default='0',nullable=False),
        sa.Column('payment_terms_days',sa.Integer(),server_default='0',nullable=False), sa.Column('is_active',sa.Boolean(),server_default=sa.true(),nullable=False),
        sa.ForeignKeyConstraint(['company_id'],['companies.id'],ondelete='CASCADE'), sa.UniqueConstraint('company_id','code',name='uq_commerce_partner_company_code'),
        sa.CheckConstraint("partner_type IN ('customer','vendor','both')",name='ck_commerce_partner_type'))
    op.create_index('ix_commerce_partners_company_id','commerce_partners',['company_id'])
    op.create_table('sales_documents',
        sa.Column('id',sa.Integer(),primary_key=True),sa.Column('company_id',sa.Integer(),nullable=False),sa.Column('partner_id',sa.Integer(),nullable=False),
        sa.Column('document_type',sa.String(20),nullable=False),sa.Column('number',sa.String(60),nullable=False),sa.Column('document_date',sa.Date(),nullable=False),
        sa.Column('status',sa.String(20),nullable=False,server_default='draft'),sa.Column('warehouse_id',sa.Integer()),sa.Column('notes',sa.Text()),
        sa.Column('subtotal',sa.Numeric(18,4),nullable=False,server_default='0'),sa.Column('tax_total',sa.Numeric(18,4),nullable=False,server_default='0'),
        sa.Column('discount_total',sa.Numeric(18,4),nullable=False,server_default='0'),sa.Column('total',sa.Numeric(18,4),nullable=False,server_default='0'),sa.Column('paid_total',sa.Numeric(18,4),nullable=False,server_default='0'),
        sa.ForeignKeyConstraint(['company_id'],['companies.id'],ondelete='CASCADE'),sa.ForeignKeyConstraint(['partner_id'],['commerce_partners.id'],ondelete='RESTRICT'),sa.ForeignKeyConstraint(['warehouse_id'],['inventory_warehouses.id'],ondelete='RESTRICT'),
        sa.UniqueConstraint('company_id','number',name='uq_sales_document_company_number'),sa.CheckConstraint("document_type IN ('quotation','order','delivery','invoice','credit_note')",name='ck_sales_document_type'),sa.CheckConstraint("status IN ('draft','confirmed','partially_fulfilled','fulfilled','cancelled','posted')",name='ck_sales_document_status'))
    op.create_index('ix_sales_documents_company_id','sales_documents',['company_id']);op.create_index('ix_sales_documents_partner_id','sales_documents',['partner_id']);op.create_index('ix_sales_documents_number','sales_documents',['number'])
    op.create_table('sales_lines',
        sa.Column('id',sa.Integer(),primary_key=True),sa.Column('document_id',sa.Integer(),nullable=False),sa.Column('item_id',sa.Integer(),nullable=False),sa.Column('description',sa.String(250)),sa.Column('quantity',sa.Numeric(18,4),nullable=False),sa.Column('unit_price',sa.Numeric(18,4),nullable=False),sa.Column('discount_percent',sa.Numeric(8,4),nullable=False,server_default='0'),sa.Column('tax_percent',sa.Numeric(8,4),nullable=False,server_default='0'),sa.Column('line_total',sa.Numeric(18,4),nullable=False,server_default='0'),
        sa.ForeignKeyConstraint(['document_id'],['sales_documents.id'],ondelete='CASCADE'),sa.ForeignKeyConstraint(['item_id'],['inventory_items.id'],ondelete='RESTRICT'),sa.CheckConstraint('quantity > 0',name='ck_sales_line_qty'),sa.CheckConstraint('unit_price >= 0',name='ck_sales_line_price'))
    op.create_index('ix_sales_lines_document_id','sales_lines',['document_id']);op.create_index('ix_sales_lines_item_id','sales_lines',['item_id'])
    op.create_table('purchase_documents',
        sa.Column('id',sa.Integer(),primary_key=True),sa.Column('company_id',sa.Integer(),nullable=False),sa.Column('partner_id',sa.Integer(),nullable=False),sa.Column('document_type',sa.String(20),nullable=False),sa.Column('number',sa.String(60),nullable=False),sa.Column('document_date',sa.Date(),nullable=False),sa.Column('status',sa.String(20),nullable=False,server_default='draft'),sa.Column('warehouse_id',sa.Integer()),sa.Column('notes',sa.Text()),sa.Column('subtotal',sa.Numeric(18,4),nullable=False,server_default='0'),sa.Column('tax_total',sa.Numeric(18,4),nullable=False,server_default='0'),sa.Column('discount_total',sa.Numeric(18,4),nullable=False,server_default='0'),sa.Column('total',sa.Numeric(18,4),nullable=False,server_default='0'),sa.Column('paid_total',sa.Numeric(18,4),nullable=False,server_default='0'),
        sa.ForeignKeyConstraint(['company_id'],['companies.id'],ondelete='CASCADE'),sa.ForeignKeyConstraint(['partner_id'],['commerce_partners.id'],ondelete='RESTRICT'),sa.ForeignKeyConstraint(['warehouse_id'],['inventory_warehouses.id'],ondelete='RESTRICT'),sa.UniqueConstraint('company_id','number',name='uq_purchase_document_company_number'),sa.CheckConstraint("document_type IN ('requisition','rfq','order','receipt','bill','debit_note')",name='ck_purchase_document_type'),sa.CheckConstraint("status IN ('draft','confirmed','partially_received','received','cancelled','posted')",name='ck_purchase_document_status'))
    op.create_index('ix_purchase_documents_company_id','purchase_documents',['company_id']);op.create_index('ix_purchase_documents_partner_id','purchase_documents',['partner_id'])
    op.create_table('purchase_lines',sa.Column('id',sa.Integer(),primary_key=True),sa.Column('document_id',sa.Integer(),nullable=False),sa.Column('item_id',sa.Integer(),nullable=False),sa.Column('description',sa.String(250)),sa.Column('quantity',sa.Numeric(18,4),nullable=False),sa.Column('unit_price',sa.Numeric(18,4),nullable=False),sa.Column('discount_percent',sa.Numeric(8,4),nullable=False,server_default='0'),sa.Column('tax_percent',sa.Numeric(8,4),nullable=False,server_default='0'),sa.Column('line_total',sa.Numeric(18,4),nullable=False,server_default='0'),sa.ForeignKeyConstraint(['document_id'],['purchase_documents.id'],ondelete='CASCADE'),sa.ForeignKeyConstraint(['item_id'],['inventory_items.id'],ondelete='RESTRICT'),sa.CheckConstraint('quantity > 0',name='ck_purchase_line_qty'))
    op.create_index('ix_purchase_lines_document_id','purchase_lines',['document_id']);op.create_index('ix_purchase_lines_item_id','purchase_lines',['item_id'])
    op.create_table('commerce_payments',sa.Column('id',sa.Integer(),primary_key=True),sa.Column('company_id',sa.Integer(),nullable=False),sa.Column('document_kind',sa.String(10),nullable=False),sa.Column('document_id',sa.Integer(),nullable=False),sa.Column('payment_date',sa.Date(),nullable=False),sa.Column('amount',sa.Numeric(18,4),nullable=False),sa.Column('method',sa.String(30),nullable=False),sa.Column('reference',sa.String(100)),sa.Column('notes',sa.Text()),sa.ForeignKeyConstraint(['company_id'],['companies.id'],ondelete='CASCADE'),sa.CheckConstraint("document_kind IN ('sale','purchase')",name='ck_commerce_payment_kind'),sa.CheckConstraint('amount > 0',name='ck_commerce_payment_amount'))
    op.create_index('ix_commerce_payments_company_id','commerce_payments',['company_id']);op.create_index('ix_commerce_payments_document_id','commerce_payments',['document_id'])

def downgrade():
    op.drop_table('commerce_payments');op.drop_table('purchase_lines');op.drop_table('purchase_documents');op.drop_table('sales_lines');op.drop_table('sales_documents');op.drop_table('commerce_partners')
