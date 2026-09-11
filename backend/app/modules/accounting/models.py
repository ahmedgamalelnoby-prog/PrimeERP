from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from app.database.base import Base

class JournalEntry(Base):
    __tablename__='journal_entries'
    id=Column(Integer,primary_key=True); company_id=Column(Integer,ForeignKey('companies.id',ondelete='CASCADE'),nullable=False,index=True); entry_no=Column(String(60),nullable=False,index=True); entry_date=Column(DateTime,nullable=False); source_type=Column(String(40)); source_id=Column(Integer); description=Column(Text); status=Column(String(20),nullable=False,server_default='draft'); total_debit=Column(Numeric(18,4),nullable=False,server_default='0'); total_credit=Column(Numeric(18,4),nullable=False,server_default='0')
    __table_args__=(CheckConstraint("status IN ('draft','posted','reversed')",name='ck_je_status'),)
class JournalLine(Base):
    __tablename__='journal_lines'
    id=Column(Integer,primary_key=True); journal_entry_id=Column(Integer,ForeignKey('journal_entries.id',ondelete='CASCADE'),nullable=False,index=True); account_id=Column(Integer,nullable=False,index=True); description=Column(String(250)); debit=Column(Numeric(18,4),nullable=False,server_default='0'); credit=Column(Numeric(18,4),nullable=False,server_default='0')
    __table_args__=(CheckConstraint('debit >= 0 AND credit >= 0',name='ck_jl_nonnegative'),CheckConstraint('(debit = 0) OR (credit = 0)',name='ck_jl_one_side'),)
class TaxRate(Base):
    __tablename__='tax_rates'
    id=Column(Integer,primary_key=True); company_id=Column(Integer,ForeignKey('companies.id',ondelete='CASCADE'),nullable=False,index=True); code=Column(String(40),nullable=False); name=Column(String(120),nullable=False); rate=Column(Numeric(8,4),nullable=False); tax_type=Column(String(20),nullable=False,server_default='vat'); is_withholding=Column(Boolean,nullable=False,server_default='false'); is_active=Column(Boolean,nullable=False,server_default='true')
    __table_args__=(CheckConstraint('rate >= 0',name='ck_tax_rate_nonnegative'),)
