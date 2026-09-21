from sqlalchemy import Boolean,Column,Date,DateTime,ForeignKey,Integer,Numeric,String
from sqlalchemy.sql import func
from app.database.base import Base
class AccountingRecognitionSchedule(Base):
 __tablename__="accounting_recognition_schedules"
 id=Column(Integer,primary_key=True);tenant_id=Column(Integer,ForeignKey("tenants.id",ondelete="CASCADE"),nullable=False,index=True);company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
 kind=Column(String(20),nullable=False);name=Column(String(160),nullable=False);journal_id=Column(Integer,ForeignKey("accounting_journals.id",ondelete="RESTRICT"),nullable=False);branch_id=Column(Integer,ForeignKey("branches.id",ondelete="RESTRICT"),nullable=False)
 debit_account_id=Column(Integer,nullable=False);credit_account_id=Column(Integer,nullable=False);total_amount=Column(Numeric(20,6),nullable=False);period_count=Column(Integer,nullable=False);recognized_periods=Column(Integer,nullable=False,default=0);next_run_date=Column(Date,nullable=False);end_date=Column(Date);currency_code=Column(String(3),nullable=False,default="EGP");active=Column(Boolean,nullable=False,default=True);source_reference=Column(String(160));created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
