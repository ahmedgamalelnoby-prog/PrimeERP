from sqlalchemy import Column,Integer,String,Numeric,Date,Boolean,ForeignKey,Text
from sqlalchemy.sql import func
from sqlalchemy import DateTime
from app.database.base import Base
class JournalAutomation(Base):
    __tablename__="journal_automations"
    id=Column(Integer,primary_key=True); company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True); kind=Column(String(20),nullable=False); name=Column(String(160),nullable=False); journal_id=Column(Integer,ForeignKey("accounting_journals.id",ondelete="RESTRICT"),nullable=False); branch_id=Column(Integer,ForeignKey("branches.id",ondelete="RESTRICT"),nullable=False); start_date=Column(Date,nullable=False); end_date=Column(Date); frequency=Column(String(20),nullable=False,default="monthly"); amount=Column(Numeric(20,6),nullable=False); debit_account_id=Column(Integer,nullable=False); credit_account_id=Column(Integer,nullable=False); currency_code=Column(String(3),nullable=False,default="EGP"); status=Column(String(20),nullable=False,default="active"); description=Column(Text); created_at=Column(DateTime(timezone=True),nullable=False,server_default=func.now())
class JournalAllocation(Base):
    __tablename__="journal_allocations"
    id=Column(Integer,primary_key=True); company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True); source_entry_id=Column(Integer,ForeignKey("journal_entries.id",ondelete="CASCADE"),nullable=False); target_account_id=Column(Integer,nullable=False); amount=Column(Numeric(20,6),nullable=False); dimension_key=Column(String(100)); status=Column(String(20),nullable=False,default="draft"); created_at=Column(DateTime(timezone=True),nullable=False,server_default=func.now())
