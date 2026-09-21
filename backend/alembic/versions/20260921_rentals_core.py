from alembic import op
import sqlalchemy as sa

revision="20260921_rentals_core"
down_revision="20260920_release_gate_merge"
branch_labels=None
depends_on=None

def upgrade():
    op.create_table("rental_properties",
        sa.Column("id",sa.Integer(),primary_key=True),
        sa.Column("tenant_id",sa.Integer(),sa.ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False),
        sa.Column("company_id",sa.Integer(),sa.ForeignKey("companies.id",ondelete="CASCADE"),nullable=False),
        sa.Column("branch_id",sa.Integer(),sa.ForeignKey("branches.id",ondelete="RESTRICT")),
        sa.Column("code",sa.String(60),nullable=False),sa.Column("name",sa.String(200),nullable=False),
        sa.Column("address",sa.Text()),sa.Column("is_active",sa.Boolean(),nullable=False,server_default=sa.true()),
        sa.UniqueConstraint("company_id","code",name="uq_rental_property_company_code"))
    op.create_index("ix_rental_properties_tenant_id","rental_properties",["tenant_id"])
    op.create_index("ix_rental_properties_company_id","rental_properties",["company_id"])
    op.create_table("rental_units",
        sa.Column("id",sa.Integer(),primary_key=True),sa.Column("tenant_id",sa.Integer(),sa.ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False),
        sa.Column("company_id",sa.Integer(),sa.ForeignKey("companies.id",ondelete="CASCADE"),nullable=False),sa.Column("property_id",sa.Integer(),sa.ForeignKey("rental_properties.id",ondelete="CASCADE"),nullable=False),
        sa.Column("code",sa.String(60),nullable=False),sa.Column("name",sa.String(200),nullable=False),sa.Column("unit_type",sa.String(40),nullable=False,server_default="commercial"),sa.Column("area",sa.Numeric(18,4)),sa.Column("status",sa.String(30),nullable=False,server_default="available"),sa.Column("is_active",sa.Boolean(),nullable=False,server_default=sa.true()),
        sa.UniqueConstraint("company_id","property_id","code",name="uq_rental_unit_property_code"),sa.CheckConstraint("status IN ('available','occupied','reserved','maintenance','inactive')",name="ck_rental_unit_status"))
    op.create_index("ix_rental_units_tenant_id","rental_units",["tenant_id"]); op.create_index("ix_rental_units_company_id","rental_units",["company_id"])
    op.create_table("rental_tenants",
        sa.Column("id",sa.Integer(),primary_key=True),sa.Column("tenant_id",sa.Integer(),sa.ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False),sa.Column("company_id",sa.Integer(),sa.ForeignKey("companies.id",ondelete="CASCADE"),nullable=False),
        sa.Column("partner_id",sa.Integer(),sa.ForeignKey("commerce_partners.id",ondelete="RESTRICT")),sa.Column("code",sa.String(60),nullable=False),sa.Column("name",sa.String(200),nullable=False),sa.Column("tax_number",sa.String(80)),sa.Column("phone",sa.String(60)),sa.Column("email",sa.String(200)),sa.Column("is_active",sa.Boolean(),nullable=False,server_default=sa.true()),sa.UniqueConstraint("company_id","code",name="uq_rental_tenant_company_code"))
    op.create_index("ix_rental_tenants_tenant_id","rental_tenants",["tenant_id"]); op.create_index("ix_rental_tenants_company_id","rental_tenants",["company_id"])
    op.create_table("rental_contracts",
        sa.Column("id",sa.Integer(),primary_key=True),sa.Column("tenant_id",sa.Integer(),sa.ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False),sa.Column("company_id",sa.Integer(),sa.ForeignKey("companies.id",ondelete="CASCADE"),nullable=False),
        sa.Column("branch_id",sa.Integer(),sa.ForeignKey("branches.id",ondelete="RESTRICT")),sa.Column("unit_id",sa.Integer(),sa.ForeignKey("rental_units.id",ondelete="RESTRICT"),nullable=False),sa.Column("rental_tenant_id",sa.Integer(),sa.ForeignKey("rental_tenants.id",ondelete="RESTRICT"),nullable=False),
        sa.Column("number",sa.String(80),nullable=False),sa.Column("start_date",sa.Date(),nullable=False),sa.Column("end_date",sa.Date(),nullable=False),sa.Column("status",sa.String(30),nullable=False,server_default="draft"),sa.Column("pricing_type",sa.String(30),nullable=False,server_default="fixed"),
        sa.Column("fixed_rent",sa.Numeric(18,4),nullable=False,server_default="0"),sa.Column("minimum_guarantee",sa.Numeric(18,4),nullable=False,server_default="0"),sa.Column("revenue_share_percent",sa.Numeric(8,4),nullable=False,server_default="0"),sa.Column("maintenance_amount",sa.Numeric(18,4),nullable=False,server_default="0"),sa.Column("security_deposit",sa.Numeric(18,4),nullable=False,server_default="0"),sa.Column("vat_percent",sa.Numeric(8,4),nullable=False,server_default="0"),sa.Column("wht_percent",sa.Numeric(8,4),nullable=False,server_default="0"),sa.Column("notes",sa.Text()),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
        sa.UniqueConstraint("company_id","number",name="uq_rental_contract_company_number"),sa.CheckConstraint("end_date >= start_date",name="ck_rental_contract_dates"),sa.CheckConstraint("pricing_type IN ('fixed','minimum_guarantee','revenue_share','fixed_plus_revenue_share')",name="ck_rental_contract_pricing_type"),sa.CheckConstraint("revenue_share_percent >= 0 AND revenue_share_percent <= 100",name="ck_rental_contract_share"))
    op.create_index("ix_rental_contracts_tenant_id","rental_contracts",["tenant_id"]); op.create_index("ix_rental_contracts_company_id","rental_contracts",["company_id"])
    op.create_table("rental_charges",
        sa.Column("id",sa.Integer(),primary_key=True),sa.Column("tenant_id",sa.Integer(),sa.ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False),sa.Column("company_id",sa.Integer(),sa.ForeignKey("companies.id",ondelete="CASCADE"),nullable=False),sa.Column("contract_id",sa.Integer(),sa.ForeignKey("rental_contracts.id",ondelete="CASCADE"),nullable=False),sa.Column("charge_date",sa.Date(),nullable=False),sa.Column("period_start",sa.Date(),nullable=False),sa.Column("period_end",sa.Date(),nullable=False),
        sa.Column("base_amount",sa.Numeric(18,4),nullable=False),sa.Column("revenue_amount",sa.Numeric(18,4),nullable=False,server_default="0"),sa.Column("maintenance_amount",sa.Numeric(18,4),nullable=False,server_default="0"),sa.Column("vat_amount",sa.Numeric(18,4),nullable=False,server_default="0"),sa.Column("wht_amount",sa.Numeric(18,4),nullable=False,server_default="0"),sa.Column("total_amount",sa.Numeric(18,4),nullable=False),sa.Column("status",sa.String(30),nullable=False,server_default="draft"),
        sa.UniqueConstraint("contract_id","period_start","period_end",name="uq_rental_charge_contract_period"),sa.CheckConstraint("base_amount >= 0",name="ck_rental_charge_base"),sa.CheckConstraint("total_amount >= 0",name="ck_rental_charge_total"))
    op.create_index("ix_rental_charges_tenant_id","rental_charges",["tenant_id"]); op.create_index("ix_rental_charges_company_id","rental_charges",["company_id"])

def downgrade():
    op.drop_table("rental_charges"); op.drop_table("rental_contracts"); op.drop_table("rental_tenants"); op.drop_table("rental_units"); op.drop_table("rental_properties")
