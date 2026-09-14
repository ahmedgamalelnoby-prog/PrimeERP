"""global jurisdiction and effective-dated tax rules

Revision ID: 20260914_global_jurisdiction
Revises: 20260914_variant_inventory_dimension
"""
from alembic import op
import sqlalchemy as sa

revision = "20260914_global_jurisdiction"
down_revision = "20260914_variant_inventory_dimension"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("jurisdictions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("country_code", sa.String(2), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("default_currency", sa.String(3), nullable=False),
        sa.Column("timezone", sa.String(80)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.CheckConstraint("length(country_code) = 2", name="ck_jurisdiction_country_code"),
        sa.CheckConstraint("length(default_currency) = 3", name="ck_jurisdiction_currency"),
        sa.UniqueConstraint("code", name="uq_jurisdictions_code"),
    )
    op.create_index("ix_jurisdictions_country_code", "jurisdictions", ["country_code"])
    op.create_table("company_jurisdictions",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("jurisdiction_id", sa.Integer(), sa.ForeignKey("jurisdictions.id", ondelete="RESTRICT"), nullable=False), sa.Column("role", sa.String(30), nullable=False, server_default="primary"),
        sa.Column("effective_from", sa.Date(), nullable=False), sa.Column("effective_to", sa.Date()), sa.Column("tax_resident", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("vat_registered", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("tax_ids", sa.JSON(), nullable=False, server_default=sa.text("'{}'")), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.CheckConstraint("role IN ('primary','tax','permanent_establishment','registration')", name="ck_company_jurisdiction_role"),
        sa.UniqueConstraint("company_id", "jurisdiction_id", "role", "effective_from", name="uq_company_jurisdiction_version"),
    )
    op.create_index("ix_company_jurisdictions_company_id", "company_jurisdictions", ["company_id"])
    op.create_index("ix_company_jurisdictions_jurisdiction_id", "company_jurisdictions", ["jurisdiction_id"])
    op.create_table("partner_jurisdictions",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("partner_id", sa.Integer(), sa.ForeignKey("commerce_partners.id", ondelete="CASCADE"), nullable=False),
        sa.Column("jurisdiction_id", sa.Integer(), sa.ForeignKey("jurisdictions.id", ondelete="RESTRICT"), nullable=False), sa.Column("role", sa.String(30), nullable=False, server_default="residence"),
        sa.Column("effective_from", sa.Date(), nullable=False), sa.Column("effective_to", sa.Date()), sa.Column("tax_resident", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("vat_registered", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("tax_ids", sa.JSON(), nullable=False, server_default=sa.text("'{}'")), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.CheckConstraint("role IN ('residence','tax','establishment','registration')", name="ck_partner_jurisdiction_role"),
        sa.UniqueConstraint("partner_id", "jurisdiction_id", "role", "effective_from", name="uq_partner_jurisdiction_version"),
    )
    op.create_index("ix_partner_jurisdictions_partner_id", "partner_jurisdictions", ["partner_id"])
    op.create_index("ix_partner_jurisdictions_jurisdiction_id", "partner_jurisdictions", ["jurisdiction_id"])
    op.create_table("jurisdiction_tax_rules",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("jurisdiction_id", sa.Integer(), sa.ForeignKey("jurisdictions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(80), nullable=False), sa.Column("name", sa.String(200), nullable=False), sa.Column("tax_type", sa.String(30), nullable=False), sa.Column("transaction_type", sa.String(40), nullable=False),
        sa.Column("taxpayer_type", sa.String(20), nullable=False, server_default="both"), sa.Column("place_of_supply", sa.String(30), nullable=False, server_default="local"), sa.Column("rate", sa.Numeric(12,6), nullable=False, server_default="0"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"), sa.Column("conditions", sa.JSON(), nullable=False, server_default=sa.text("'{}'")), sa.Column("effective_from", sa.Date(), nullable=False), sa.Column("effective_to", sa.Date()),
        sa.Column("source_reference", sa.String(500)), sa.Column("version", sa.String(40), nullable=False, server_default="1"), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.CheckConstraint("tax_type IN ('vat','gst','sales_tax','wht','customs','other')", name="ck_tax_rule_type"), sa.CheckConstraint("taxpayer_type IN ('b2b','b2c','both')", name="ck_tax_rule_taxpayer"), sa.CheckConstraint("rate >= 0", name="ck_tax_rule_rate"),
        sa.UniqueConstraint("jurisdiction_id", "code", "effective_from", name="uq_tax_rule_version"),
    )
    op.create_index("ix_jurisdiction_tax_rules_jurisdiction_id", "jurisdiction_tax_rules", ["jurisdiction_id"])
    op.create_table("jurisdiction_decisions",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False), sa.Column("partner_id", sa.Integer(), sa.ForeignKey("commerce_partners.id", ondelete="SET NULL")),
        sa.Column("jurisdiction_id", sa.Integer(), sa.ForeignKey("jurisdictions.id", ondelete="RESTRICT"), nullable=False), sa.Column("transaction_type", sa.String(40), nullable=False), sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("place_of_supply", sa.String(30), nullable=False), sa.Column("b2b", sa.Boolean(), nullable=False), sa.Column("rationale", sa.JSON(), nullable=False, server_default=sa.text("'{}'")), sa.Column("rule_ids", sa.JSON(), nullable=False, server_default=sa.text("'[]'")), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    for table, col in [("jurisdiction_decisions","company_id"),("jurisdiction_decisions","partner_id"),("jurisdiction_decisions","jurisdiction_id")]: op.create_index(f"ix_{table}_{col}", table, [col])


def downgrade():
    op.drop_table("jurisdiction_decisions")
    op.drop_table("jurisdiction_tax_rules")
    op.drop_table("partner_jurisdictions")
    op.drop_table("company_jurisdictions")
    op.drop_table("jurisdictions")
