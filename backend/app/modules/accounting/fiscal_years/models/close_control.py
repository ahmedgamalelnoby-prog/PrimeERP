from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.sql import func
from app.database.base import Base

class FiscalYearCloseChecklistItem(Base):
    __tablename__="fiscal_year_close_checklist_items"
    id=Column(Integer,primary_key=True)
    tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    fiscal_year_id=Column(Integer,ForeignKey("fiscal_years.id",ondelete="CASCADE"),nullable=False,index=True)
    key=Column(String(80),nullable=False)
    name=Column(String(200),nullable=False)
    required=Column(Boolean,nullable=False,default=True)
    status=Column(String(20),nullable=False,default="pending")
    details=Column(Text)
    checked_by=Column(Integer,ForeignKey("users.id",ondelete="SET NULL"))
    checked_at=Column(DateTime(timezone=True))
    created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    __table_args__=(UniqueConstraint("tenant_id","company_id","fiscal_year_id","key",name="uq_fy_close_checklist"),)

class FiscalYearCloseRun(Base):
    __tablename__="fiscal_year_close_runs"
    id=Column(Integer,primary_key=True)
    tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    fiscal_year_id=Column(Integer,ForeignKey("fiscal_years.id",ondelete="CASCADE"),nullable=False,index=True)
    status=Column(String(30),nullable=False,default="precheck")
    reason=Column(Text)
    closing_entry_id=Column(Integer,ForeignKey("journal_entries.id",ondelete="SET NULL"))
    initiated_by=Column(Integer,ForeignKey("users.id",ondelete="SET NULL"))
    completed_by=Column(Integer,ForeignKey("users.id",ondelete="SET NULL"))
    initiated_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    completed_at=Column(DateTime(timezone=True))
    __table_args__=(UniqueConstraint("tenant_id","company_id","fiscal_year_id",name="uq_fy_close_run"),)

class FiscalYearCloseAudit(Base):
    __tablename__="fiscal_year_close_audits"
    id=Column(Integer,primary_key=True)
    tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    fiscal_year_id=Column(Integer,ForeignKey("fiscal_years.id",ondelete="CASCADE"),nullable=False,index=True)
    period_id=Column(Integer,ForeignKey("accounting_periods.id",ondelete="SET NULL"))
    action=Column(String(50),nullable=False)
    from_status=Column(String(30))
    to_status=Column(String(30))
    reason=Column(Text)
    actor_id=Column(Integer,ForeignKey("users.id",ondelete="SET NULL"))
    metadata_json=Column(Text)
    created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False,index=True)
