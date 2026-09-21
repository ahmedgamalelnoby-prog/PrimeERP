from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.sql import func
from app.database.base import Base

class AccountingAutoPostRule(Base):
    __tablename__="accounting_auto_post_rules"
    id=Column(Integer,primary_key=True); tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True); company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    name=Column(String(160),nullable=False); source_module=Column(String(80),nullable=False); source_entity=Column(String(80),nullable=False); journal_id=Column(Integer,ForeignKey("accounting_journals.id",ondelete="RESTRICT"),nullable=False); branch_id=Column(Integer,ForeignKey("branches.id",ondelete="RESTRICT"),nullable=False)
    debit_account_id=Column(Integer,nullable=False); credit_account_id=Column(Integer,nullable=False); currency_code=Column(String(3),nullable=False,default="EGP"); auto_approve=Column(Boolean,nullable=False,default=True); auto_post=Column(Boolean,nullable=False,default=True); is_active=Column(Boolean,nullable=False,default=True); created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    __table_args__=(UniqueConstraint("tenant_id","company_id","source_module","source_entity","name",name="uq_accounting_auto_post_rule"),)

class AccountingFXRevaluation(Base):
    __tablename__="accounting_fx_revaluations"
    id=Column(Integer,primary_key=True); tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True); company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    revaluation_date=Column(Date,nullable=False); currency_code=Column(String(3),nullable=False); foreign_amount=Column(Numeric(20,6),nullable=False); old_rate=Column(Numeric(20,10),nullable=False); new_rate=Column(Numeric(20,10),nullable=False); old_base_amount=Column(Numeric(20,6),nullable=False); new_base_amount=Column(Numeric(20,6),nullable=False); gain_loss=Column(Numeric(20,6),nullable=False)
    journal_entry_id=Column(Integer,ForeignKey("journal_entries.id",ondelete="RESTRICT"),nullable=False); created_by=Column(Integer,ForeignKey("users.id",ondelete="SET NULL")); created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)

class AccountingIntercompanyLink(Base):
    __tablename__="accounting_intercompany_links"
    id=Column(Integer,primary_key=True); tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True); source_company_id=Column(Integer,ForeignKey("companies.id",ondelete="RESTRICT"),nullable=False); target_company_id=Column(Integer,ForeignKey("companies.id",ondelete="RESTRICT"),nullable=False)
    source_entry_id=Column(Integer,ForeignKey("journal_entries.id",ondelete="RESTRICT"),nullable=False); target_entry_id=Column(Integer,ForeignKey("journal_entries.id",ondelete="RESTRICT"),nullable=False); reference=Column(String(120),nullable=False); status=Column(String(20),nullable=False,default="posted"); created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)

class AccountingElimination(Base):
    __tablename__="accounting_eliminations"
    id=Column(Integer,primary_key=True); tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True); company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False); consolidation_key=Column(String(120),nullable=False)
    journal_entry_id=Column(Integer,ForeignKey("journal_entries.id",ondelete="RESTRICT"),nullable=False); amount=Column(Numeric(20,6),nullable=False); description=Column(Text); created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)

class AccountingPostingLink(Base):
    __tablename__="accounting_posting_links"
    id=Column(Integer,primary_key=True); tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True); company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    source_module=Column(String(80),nullable=False); source_entity=Column(String(80),nullable=False); source_id=Column(String(120),nullable=False); journal_entry_id=Column(Integer,ForeignKey("journal_entries.id",ondelete="RESTRICT"),nullable=False); reversal_entry_id=Column(Integer,ForeignKey("journal_entries.id",ondelete="RESTRICT")); status=Column(String(20),nullable=False,default="posted"); created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    __table_args__=(UniqueConstraint("tenant_id","company_id","source_module","source_entity","source_id",name="uq_accounting_posting_link"),)
