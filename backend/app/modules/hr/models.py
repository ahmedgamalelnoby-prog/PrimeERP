from sqlalchemy import Column,Date,DateTime,ForeignKey,Integer,Numeric,String,Text,UniqueConstraint,func
from app.database.base import Base
class EmploymentContract(Base):
    __tablename__="hr_employment_contracts"
    id=Column(Integer,primary_key=True)
    company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True)
    employee_id=Column(Integer,ForeignKey("employees.id",ondelete="CASCADE"),nullable=False,index=True)
    start_date=Column(Date,nullable=False); end_date=Column(Date); salary=Column(Numeric(18,4),nullable=False,default=0)
    status=Column(String(30),nullable=False,default="active"); notes=Column(Text)
    __table_args__=(UniqueConstraint("employee_id","start_date",name="uq_hr_contract_employee_start"),)
