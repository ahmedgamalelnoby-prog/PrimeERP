from sqlalchemy import Boolean, CheckConstraint, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.sql import func
from app.database.base import Base

class RentalSecurityDeposit(Base):
    __tablename__="rental_security_deposits"
    id=Column(Integer,primary_key=True); tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True); company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True); contract_id=Column(Integer,ForeignKey("rental_contracts.id",ondelete="CASCADE"),nullable=False,index=True); amount=Column(Numeric(18,4),nullable=False); received_amount=Column(Numeric(18,4),nullable=False,default=0); refunded_amount=Column(Numeric(18,4),nullable=False,default=0); status=Column(String(20),nullable=False,default="open"); due_date=Column(Date); notes=Column(Text); created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    __table_args__=(CheckConstraint("amount > 0",name="ck_rental_deposit_amount"),CheckConstraint("received_amount >= 0 AND refunded_amount >= 0 AND received_amount >= refunded_amount",name="ck_rental_deposit_balances"),CheckConstraint("status IN ('open','received','partially_refunded','refunded','forfeited')",name="ck_rental_deposit_status"),)

class RentalMaintenance(Base):
    __tablename__="rental_maintenance"
    id=Column(Integer,primary_key=True); tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True); company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True); contract_id=Column(Integer,ForeignKey("rental_contracts.id",ondelete="CASCADE"),nullable=False,index=True); unit_id=Column(Integer,ForeignKey("rental_units.id",ondelete="RESTRICT"),nullable=False,index=True); request_date=Column(Date,nullable=False); completed_date=Column(Date); category=Column(String(60),nullable=False,default="general"); description=Column(Text,nullable=False); estimated_cost=Column(Numeric(18,4),nullable=False,default=0); actual_cost=Column(Numeric(18,4),nullable=False,default=0); charge_to_tenant=Column(Boolean,nullable=False,default=False); status=Column(String(20),nullable=False,default="open")
    __table_args__=(CheckConstraint("estimated_cost >= 0 AND actual_cost >= 0",name="ck_rental_maintenance_costs"),CheckConstraint("status IN ('open','in_progress','completed','cancelled')",name="ck_rental_maintenance_status"),)

class RentalInsurance(Base):
    __tablename__="rental_insurance"
    id=Column(Integer,primary_key=True); tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True); company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True); contract_id=Column(Integer,ForeignKey("rental_contracts.id",ondelete="CASCADE"),nullable=False,index=True); policy_number=Column(String(100),nullable=False); insurer=Column(String(200),nullable=False); start_date=Column(Date,nullable=False); end_date=Column(Date,nullable=False); coverage_amount=Column(Numeric(18,4),nullable=False,default=0); premium_amount=Column(Numeric(18,4),nullable=False,default=0); status=Column(String(20),nullable=False,default="active"); notes=Column(Text)
    __table_args__=(UniqueConstraint("company_id","policy_number",name="uq_rental_insurance_policy"),CheckConstraint("end_date >= start_date",name="ck_rental_insurance_dates"),CheckConstraint("coverage_amount >= 0 AND premium_amount >= 0",name="ck_rental_insurance_amounts"),CheckConstraint("status IN ('active','expired','cancelled')",name="ck_rental_insurance_status"),)

class RentalDocument(Base):
    __tablename__="rental_documents"
    id=Column(Integer,primary_key=True); tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True); company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True); contract_id=Column(Integer,ForeignKey("rental_contracts.id",ondelete="CASCADE"),nullable=False,index=True); document_type=Column(String(60),nullable=False); document_number=Column(String(120)); file_name=Column(String(255),nullable=False); storage_key=Column(String(500),nullable=False); issue_date=Column(Date); expiry_date=Column(Date); notes=Column(Text); created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)


class RentalProperty(Base):
    __tablename__="rental_properties"
    id=Column(Integer,primary_key=True)
    tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    branch_id=Column(Integer,ForeignKey("branches.id",ondelete="RESTRICT"),nullable=True,index=True)
    code=Column(String(60),nullable=False)
    name=Column(String(200),nullable=False)
    address=Column(Text)
    is_active=Column(Boolean,nullable=False,default=True)
    __table_args__=(UniqueConstraint("company_id","code",name="uq_rental_property_company_code"),)

class RentalUnit(Base):
    __tablename__="rental_units"
    id=Column(Integer,primary_key=True)
    tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    property_id=Column(Integer,ForeignKey("rental_properties.id",ondelete="CASCADE"),nullable=False,index=True)
    code=Column(String(60),nullable=False)
    name=Column(String(200),nullable=False)
    unit_type=Column(String(40),nullable=False,default="commercial")
    area=Column(Numeric(18,4),nullable=True)
    status=Column(String(30),nullable=False,default="available")
    is_active=Column(Boolean,nullable=False,default=True)
    __table_args__=(UniqueConstraint("company_id","property_id","code",name="uq_rental_unit_property_code"),CheckConstraint("status IN ('available','occupied','reserved','maintenance','inactive')",name="ck_rental_unit_status"),)

class RentalTenant(Base):
    __tablename__="rental_tenants"
    id=Column(Integer,primary_key=True)
    tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    partner_id=Column(Integer,ForeignKey("commerce_partners.id",ondelete="RESTRICT"),nullable=True,index=True)
    code=Column(String(60),nullable=False)
    name=Column(String(200),nullable=False)
    tax_number=Column(String(80))
    phone=Column(String(60))
    email=Column(String(200))
    is_active=Column(Boolean,nullable=False,default=True)
    __table_args__=(UniqueConstraint("company_id","code",name="uq_rental_tenant_company_code"),)

class RentalContract(Base):
    __tablename__="rental_contracts"
    id=Column(Integer,primary_key=True)
    tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    branch_id=Column(Integer,ForeignKey("branches.id",ondelete="RESTRICT"),nullable=True,index=True)
    unit_id=Column(Integer,ForeignKey("rental_units.id",ondelete="RESTRICT"),nullable=False,index=True)
    rental_tenant_id=Column(Integer,ForeignKey("rental_tenants.id",ondelete="RESTRICT"),nullable=False,index=True)
    number=Column(String(80),nullable=False)
    start_date=Column(Date,nullable=False)
    end_date=Column(Date,nullable=False)
    status=Column(String(30),nullable=False,default="draft")
    pricing_type=Column(String(30),nullable=False,default="fixed")
    fixed_rent=Column(Numeric(18,4),nullable=False,default=0)
    minimum_guarantee=Column(Numeric(18,4),nullable=False,default=0)
    revenue_share_percent=Column(Numeric(8,4),nullable=False,default=0)
    maintenance_amount=Column(Numeric(18,4),nullable=False,default=0)
    security_deposit=Column(Numeric(18,4),nullable=False,default=0)
    vat_percent=Column(Numeric(8,4),nullable=False,default=0)
    wht_percent=Column(Numeric(8,4),nullable=False,default=0)
    notes=Column(Text)
    created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    __table_args__=(UniqueConstraint("company_id","number",name="uq_rental_contract_company_number"),CheckConstraint("end_date >= start_date",name="ck_rental_contract_dates"),CheckConstraint("pricing_type IN ('fixed','minimum_guarantee','revenue_share','fixed_plus_revenue_share')",name="ck_rental_contract_pricing_type"),CheckConstraint("revenue_share_percent >= 0 AND revenue_share_percent <= 100",name="ck_rental_contract_share"),)

class RentalCharge(Base):
    __tablename__="rental_charges"
    id=Column(Integer,primary_key=True)
    tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    contract_id=Column(Integer,ForeignKey("rental_contracts.id",ondelete="CASCADE"),nullable=False,index=True)
    charge_date=Column(Date,nullable=False)
    period_start=Column(Date,nullable=False)
    period_end=Column(Date,nullable=False)
    base_amount=Column(Numeric(18,4),nullable=False)
    revenue_amount=Column(Numeric(18,4),nullable=False,default=0)
    maintenance_amount=Column(Numeric(18,4),nullable=False,default=0)
    vat_amount=Column(Numeric(18,4),nullable=False,default=0)
    wht_amount=Column(Numeric(18,4),nullable=False,default=0)
    total_amount=Column(Numeric(18,4),nullable=False)
    due_date=Column(Date,nullable=True)
    status=Column(String(30),nullable=False,default="draft")
    __table_args__=(CheckConstraint("base_amount >= 0",name="ck_rental_charge_base"),CheckConstraint("total_amount >= 0",name="ck_rental_charge_total"),UniqueConstraint("contract_id","period_start","period_end",name="uq_rental_charge_contract_period"),)


class RentalReceipt(Base):
    __tablename__="rental_receipts"
    id=Column(Integer,primary_key=True)
    tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    charge_id=Column(Integer,ForeignKey("rental_charges.id",ondelete="RESTRICT"),nullable=False,index=True)
    payment_date=Column(Date,nullable=False)
    amount=Column(Numeric(18,4),nullable=False)
    method=Column(String(30),nullable=False)
    reference=Column(String(120))
    status=Column(String(20),nullable=False,default="pending")
    journal_entry_id=Column(Integer,ForeignKey("journal_entries.id",ondelete="SET NULL"),nullable=True,index=True)
    created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    __table_args__=(CheckConstraint("amount > 0",name="ck_rental_receipt_amount"),CheckConstraint("status IN ('pending','posted','reversed')",name="ck_rental_receipt_status"),)
