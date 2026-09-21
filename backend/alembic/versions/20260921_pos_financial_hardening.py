"""add reservation consumption ledger and POS payment account mappings.

Revision ID: 20260921_pos_financial_hardening
Revises: 20260921_stage7_domain_merge
"""
from alembic import op
import sqlalchemy as sa

revision = "20260921_pos_financial_hardening"
down_revision = "20260921_stage7_domain_merge"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("pos_sessions", sa.Column("closing_cash", sa.Numeric(18, 4), nullable=True))
    op.add_column("pos_sessions", sa.Column("closing_card", sa.Numeric(18, 4), nullable=True))
    op.add_column("pos_sessions", sa.Column("closing_bank", sa.Numeric(18, 4), nullable=True))
    op.add_column("pos_sessions", sa.Column("closing_other", sa.Numeric(18, 4), nullable=True))
    op.add_column("inventory_reservations", sa.Column("consumed_quantity", sa.Numeric(18, 4), nullable=False, server_default="0"))
    op.create_check_constraint("ck_inventory_reservation_consumed_quantity", "inventory_reservations", "consumed_quantity >= 0 AND consumed_quantity <= quantity")
    op.create_table(
        "inventory_reservation_consumptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reservation_id", sa.Integer(), sa.ForeignKey("inventory_reservations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("source_module", sa.String(80), nullable=False),
        sa.Column("source_entity", sa.String(80), nullable=False),
        sa.Column("source_id", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("quantity > 0", name="ck_inventory_reservation_consumption_quantity"),
        sa.UniqueConstraint("company_id","reservation_id","source_module","source_entity","source_id",name="uq_inventory_reservation_consumption_source"),
    )
    op.create_index("ix_inventory_reservation_consumptions_company_id","inventory_reservation_consumptions",["company_id"])
    op.create_index("ix_inventory_reservation_consumptions_reservation_id","inventory_reservation_consumptions",["reservation_id"])
    op.create_table(
        "pos_payment_account_mappings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("method", sa.String(20), nullable=False),
        sa.Column("account_combination_id", sa.Integer(), sa.ForeignKey("account_combinations.id", ondelete="RESTRICT"), nullable=False),
        sa.UniqueConstraint("company_id","method",name="uq_pos_payment_account_mapping"),
        sa.CheckConstraint("method IN ('cash','card','bank','other')",name="ck_pos_payment_account_mapping_method"),
    )
    op.create_index("ix_pos_payment_account_mappings_company_id","pos_payment_account_mappings",["company_id"])

def downgrade():
    op.drop_column("pos_sessions", "closing_other")
    op.drop_column("pos_sessions", "closing_bank")
    op.drop_column("pos_sessions", "closing_card")
    op.drop_column("pos_sessions", "closing_cash")
    op.drop_index("ix_pos_payment_account_mappings_company_id", table_name="pos_payment_account_mappings")
    op.drop_table("pos_payment_account_mappings")
    op.drop_index("ix_inventory_reservation_consumptions_reservation_id", table_name="inventory_reservation_consumptions")
    op.drop_index("ix_inventory_reservation_consumptions_company_id", table_name="inventory_reservation_consumptions")
    op.drop_table("inventory_reservation_consumptions")
    op.drop_constraint("ck_inventory_reservation_consumed_quantity", "inventory_reservations", type_="check")
    op.drop_column("inventory_reservations", "consumed_quantity")
