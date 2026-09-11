from sqlalchemy import Boolean, CheckConstraint, Column, Date, ForeignKey, Integer, Numeric, String, Text
from app.database.base import Base

class FixedAsset(Base):
    __tablename__='fixed_assets'
    id=Column(Integer,primary_key=True); company_id=Column(Integer,ForeignKey('companies.id',ondelete='CASCADE'),nullable=False,index=True)
    code=Column(String(50),nullable=False); name=Column(String(200),nullable=False); category=Column(String(100),nullable=False)
    acquisition_date=Column(Date,nullable=False); cost=Column(Numeric(18,4),nullable=False); residual_value=Column(Numeric(18,4),nullable=False,server_default='0'); useful_life_months=Column(Integer,nullable=False)
    depreciation_method=Column(String(30),nullable=False,server_default='straight_line'); accumulated_depreciation=Column(Numeric(18,4),nullable=False,server_default='0'); status=Column(String(20),nullable=False,server_default='active')
    __table_args__=(CheckConstraint('cost >= 0',name='ck_asset_cost'),CheckConstraint('residual_value >= 0',name='ck_asset_residual'),CheckConstraint('useful_life_months > 0',name='ck_asset_life'),CheckConstraint("status IN ('draft','active','disposed')",name='ck_asset_status'))
class Budget(Base):
    __tablename__='budgets'
    id=Column(Integer,primary_key=True); company_id=Column(Integer,ForeignKey('companies.id',ondelete='CASCADE'),nullable=False,index=True); name=Column(String(200),nullable=False); fiscal_year=Column(Integer,nullable=False); status=Column(String(20),nullable=False,server_default='draft'); notes=Column(Text)
    __table_args__=(CheckConstraint("status IN ('draft','approved','closed')",name='ck_budget_status'),)
class BudgetLine(Base):
    __tablename__='budget_lines'
    id=Column(Integer,primary_key=True); budget_id=Column(Integer,ForeignKey('budgets.id',ondelete='CASCADE'),nullable=False,index=True); account_id=Column(Integer,nullable=False); period=Column(Integer,nullable=False); amount=Column(Numeric(18,4),nullable=False); actual_amount=Column(Numeric(18,4),nullable=False,server_default='0')
class Employee(Base):
    __tablename__='employees'
    id=Column(Integer,primary_key=True); company_id=Column(Integer,ForeignKey('companies.id',ondelete='CASCADE'),nullable=False,index=True); employee_no=Column(String(50),nullable=False); name=Column(String(200),nullable=False); department=Column(String(100)); job_title=Column(String(120)); hire_date=Column(Date,nullable=False); basic_salary=Column(Numeric(18,4),nullable=False,server_default='0'); allowances=Column(Numeric(18,4),nullable=False,server_default='0'); deductions=Column(Numeric(18,4),nullable=False,server_default='0'); is_active=Column(Boolean,nullable=False,server_default='true')
class PayrollRun(Base):
    __tablename__='payroll_runs'
    id=Column(Integer,primary_key=True); company_id=Column(Integer,ForeignKey('companies.id',ondelete='CASCADE'),nullable=False,index=True); period=Column(String(20),nullable=False); status=Column(String(20),nullable=False,server_default='draft'); total_gross=Column(Numeric(18,4),nullable=False,server_default='0'); total_deductions=Column(Numeric(18,4),nullable=False,server_default='0'); total_net=Column(Numeric(18,4),nullable=False,server_default='0')
class PayrollLine(Base):
    __tablename__='payroll_lines'
    id=Column(Integer,primary_key=True); payroll_run_id=Column(Integer,ForeignKey('payroll_runs.id',ondelete='CASCADE'),nullable=False,index=True); employee_id=Column(Integer,ForeignKey('employees.id',ondelete='RESTRICT'),nullable=False); gross=Column(Numeric(18,4),nullable=False); deductions=Column(Numeric(18,4),nullable=False); net=Column(Numeric(18,4),nullable=False)
class Project(Base):
    __tablename__='projects'
    id=Column(Integer,primary_key=True); company_id=Column(Integer,ForeignKey('companies.id',ondelete='CASCADE'),nullable=False,index=True); code=Column(String(50),nullable=False); name=Column(String(200),nullable=False); customer_id=Column(Integer,nullable=True); start_date=Column(Date); end_date=Column(Date); budget=Column(Numeric(18,4),nullable=False,server_default='0'); actual_cost=Column(Numeric(18,4),nullable=False,server_default='0'); status=Column(String(20),nullable=False,server_default='draft'); description=Column(Text)
class ProjectContract(Base):
    __tablename__='project_contracts'
    id=Column(Integer,primary_key=True); company_id=Column(Integer,ForeignKey('companies.id',ondelete='CASCADE'),nullable=False,index=True); project_id=Column(Integer,ForeignKey('projects.id',ondelete='CASCADE'),nullable=False,index=True); contract_no=Column(String(80),nullable=False); customer_id=Column(Integer,nullable=True); contract_value=Column(Numeric(18,4),nullable=False); start_date=Column(Date); end_date=Column(Date); retention_percent=Column(Numeric(8,4),nullable=False,server_default='0'); status=Column(String(20),nullable=False,server_default='draft'); terms=Column(Text)
