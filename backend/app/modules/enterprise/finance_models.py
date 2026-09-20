from sqlalchemy import Boolean,CheckConstraint,Column,Date,DateTime,ForeignKey,Integer,Numeric,String,Text,UniqueConstraint,func
from app.database.base import Base
class FinanceEntity(Base):
    __tablename__="finance_entities"
    id=Column(Integer,primary_key=True);company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True);code=Column(String(40),nullable=False);name=Column(String(160),nullable=False);functional_currency=Column(String(3),nullable=False,server_default="EGP");consolidation_method=Column(String(30),nullable=False,server_default="full");is_active=Column(Boolean,nullable=False,server_default="true")
    __table_args__=(UniqueConstraint("company_id","code",name="uq_finance_entity_company_code"),CheckConstraint("consolidation_method IN ('full','proportionate','equity')",name="ck_finance_entity_method"),)
class ConsolidationGroup(Base):
    __tablename__="consolidation_groups"
    id=Column(Integer,primary_key=True);company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True);code=Column(String(40),nullable=False);name=Column(String(160),nullable=False);reporting_currency=Column(String(3),nullable=False,server_default="EGP");is_active=Column(Boolean,nullable=False,server_default="true")
    __table_args__=(UniqueConstraint("company_id","code",name="uq_consolidation_group_company_code"),)
class ConsolidationMember(Base):
    __tablename__="consolidation_members"
    id=Column(Integer,primary_key=True);group_id=Column(Integer,ForeignKey("consolidation_groups.id",ondelete="CASCADE"),nullable=False,index=True);entity_id=Column(Integer,ForeignKey("finance_entities.id",ondelete="RESTRICT"),nullable=False,index=True);ownership_percent=Column(Numeric(8,4),nullable=False,server_default="100");consolidation_percent=Column(Numeric(8,4),nullable=False,server_default="100");active_from=Column(Date);active_to=Column(Date);is_active=Column(Boolean,nullable=False,server_default="true")
    __table_args__=(UniqueConstraint("group_id","entity_id",name="uq_consolidation_member"),CheckConstraint("ownership_percent >= 0 AND ownership_percent <= 100",name="ck_consolidation_ownership"),CheckConstraint("consolidation_percent >= 0 AND consolidation_percent <= 100",name="ck_consolidation_percent"),)
class IntercompanyTransaction(Base):
    __tablename__="intercompany_transactions"
    id=Column(Integer,primary_key=True);company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True);from_entity_id=Column(Integer,ForeignKey("finance_entities.id",ondelete="RESTRICT"),nullable=False);to_entity_id=Column(Integer,ForeignKey("finance_entities.id",ondelete="RESTRICT"),nullable=False);reference=Column(String(160),nullable=False);transaction_date=Column(Date,nullable=False);account_code=Column(String(40),nullable=False);amount=Column(Numeric(20,4),nullable=False);currency_code=Column(String(3),nullable=False,server_default="EGP");status=Column(String(20),nullable=False,server_default="open");description=Column(Text)
    __table_args__=(CheckConstraint("amount >= 0",name="ck_intercompany_amount"),CheckConstraint("status IN ('open','matched','eliminated','cancelled')",name="ck_intercompany_status"),)
class ConsolidationRun(Base):
    __tablename__="consolidation_runs"
    id=Column(Integer,primary_key=True);group_id=Column(Integer,ForeignKey("consolidation_groups.id",ondelete="RESTRICT"),nullable=False,index=True);period_start=Column(Date,nullable=False);period_end=Column(Date,nullable=False);status=Column(String(20),nullable=False,server_default="draft");total_debit=Column(Numeric(20,4),nullable=False,server_default="0");total_credit=Column(Numeric(20,4),nullable=False,server_default="0");elimination_total=Column(Numeric(20,4),nullable=False,server_default="0");created_by=Column(Integer,ForeignKey("users.id",ondelete="SET NULL"));created_at=Column(DateTime,nullable=False,server_default=func.now())
    __table_args__=(CheckConstraint("period_end >= period_start",name="ck_consolidation_period"),CheckConstraint("status IN ('draft','calculated','approved','closed')",name="ck_consolidation_run_status"),)
class ConsolidationLine(Base):
    __tablename__="consolidation_lines"
    id=Column(Integer,primary_key=True);run_id=Column(Integer,ForeignKey("consolidation_runs.id",ondelete="CASCADE"),nullable=False,index=True);account_code=Column(String(40),nullable=False);debit=Column(Numeric(20,4),nullable=False,server_default="0");credit=Column(Numeric(20,4),nullable=False,server_default="0");source_company_id=Column(Integer,ForeignKey("companies.id",ondelete="RESTRICT"));ownership_percent=Column(Numeric(8,4),nullable=False,server_default="100")
    __table_args__=(UniqueConstraint("run_id","account_code","source_company_id",name="uq_consolidation_line_source"),)
class ConsolidationElimination(Base):
    __tablename__="consolidation_eliminations"
    id=Column(Integer,primary_key=True);run_id=Column(Integer,ForeignKey("consolidation_runs.id",ondelete="CASCADE"),nullable=False,index=True);intercompany_transaction_id=Column(Integer,ForeignKey("intercompany_transactions.id",ondelete="RESTRICT"),nullable=True);account_code=Column(String(40),nullable=False);debit=Column(Numeric(20,4),nullable=False,server_default="0");credit=Column(Numeric(20,4),nullable=False,server_default="0");reason=Column(String(300),nullable=False)
class FinanceFxRate(Base):
    __tablename__="finance_fx_rates"
    id=Column(Integer,primary_key=True);company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True);rate_date=Column(Date,nullable=False);from_currency=Column(String(3),nullable=False);to_currency=Column(String(3),nullable=False);rate=Column(Numeric(20,10),nullable=False)
    __table_args__=(UniqueConstraint("company_id","rate_date","from_currency","to_currency",name="uq_finance_fx_rate"),CheckConstraint("rate > 0",name="ck_finance_fx_positive"),)
class FinanceRevaluation(Base):
    __tablename__="finance_revaluations"
    id=Column(Integer,primary_key=True);company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True);revaluation_date=Column(Date,nullable=False);account_code=Column(String(40),nullable=False);currency_code=Column(String(3),nullable=False);base_amount=Column(Numeric(20,4),nullable=False);old_rate=Column(Numeric(20,10),nullable=False);new_rate=Column(Numeric(20,10),nullable=False);gain_loss=Column(Numeric(20,4),nullable=False);status=Column(String(20),nullable=False,server_default="draft");reason=Column(Text)
    __table_args__=(CheckConstraint("old_rate > 0 AND new_rate > 0",name="ck_finance_revaluation_rates"),CheckConstraint("status IN ('draft','posted','reversed')",name="ck_finance_revaluation_status"),)
