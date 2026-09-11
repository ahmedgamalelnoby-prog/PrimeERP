"""add treasury cheque lifecycle and RBAC permissions

Revision ID: 20260911_treasury
Revises: 20260911_product_merge
"""
from alembic import op
import sqlalchemy as sa

revision = "20260911_treasury"
down_revision = "20260911_product_merge"
branch_labels = None
depends_on = None

PERMISSIONS = (
    ("treasury.access", "treasury", "access"),
    ("treasury.write", "treasury", "write"),
    ("treasury.post", "treasury", "post"),
    ("treasury.reverse", "treasury", "reverse"),
)


def upgrade():
    op.create_table(
        "treasury_cheques",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("partner_id", sa.Integer(), sa.ForeignKey("commerce_partners.id", ondelete="RESTRICT"), nullable=True, index=True),
        sa.Column("direction", sa.String(10), nullable=False),
        sa.Column("cheque_number", sa.String(100), nullable=False),
        sa.Column("bank_name", sa.String(150), nullable=True),
        sa.Column("account_number", sa.String(100), nullable=True),
        sa.Column("cheque_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False, server_default="EGP"),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("source_payment_id", sa.Integer(), sa.ForeignKey("commerce_payments.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("original_cheque_id", sa.Integer(), sa.ForeignKey("treasury_cheques.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("direction IN ('received','issued')", name="ck_treasury_cheque_direction"),
        sa.CheckConstraint("amount > 0", name="ck_treasury_cheque_amount"),
        sa.CheckConstraint("status IN ('received','deposited','under_collection','collected','returned','resubmitted','issued','cleared','cancelled','reversed','withdrawn')", name="ck_treasury_cheque_status"),
        sa.CheckConstraint("due_date >= cheque_date", name="ck_treasury_cheque_dates"),
    )
    op.create_table(
        "treasury_cheque_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("cheque_id", sa.Integer(), sa.ForeignKey("treasury_cheques.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("from_status", sa.String(30), nullable=True),
        sa.Column("to_status", sa.String(30), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("reference", sa.String(150), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    bind = op.get_bind()
    permissions = sa.table("permissions", sa.column("id", sa.Integer), sa.column("name", sa.String), sa.column("resource", sa.String), sa.column("action", sa.String), sa.column("is_active", sa.Boolean))
    for name, resource, action in PERMISSIONS:
        if bind.execute(sa.select(permissions.c.id).where(permissions.c.name == name)).first() is None:
            bind.execute(permissions.insert().values(name=name, resource=resource, action=action, is_active=True))


def downgrade():
    bind = op.get_bind()
    permissions = sa.table("permissions", sa.column("name", sa.String))
    bind.execute(permissions.delete().where(permissions.c.name.in_([p[0] for p in PERMISSIONS])))
    op.drop_table("treasury_cheque_events")
    op.drop_table("treasury_cheques")
