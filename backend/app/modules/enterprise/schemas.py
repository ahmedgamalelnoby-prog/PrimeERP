from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict
class AssetCreate(BaseModel):
 company_id:int=Field(gt=0); code:str; name:str; category:str; acquisition_date:date; cost:Decimal=Field(ge=0); residual_value:Decimal=Field(default=0,ge=0); useful_life_months:int=Field(gt=0)
class AssetResponse(AssetCreate):
 model_config=ConfigDict(from_attributes=True); id:int; accumulated_depreciation:Decimal; status:str
class EmployeeCreate(BaseModel):
 company_id:int=Field(gt=0); employee_no:str; name:str; department:str|None=None; job_title:str|None=None; hire_date:date; basic_salary:Decimal=Field(ge=0); allowances:Decimal=Field(default=0,ge=0); deductions:Decimal=Field(default=0,ge=0)
class EmployeeResponse(EmployeeCreate):
 model_config=ConfigDict(from_attributes=True); id:int; is_active:bool
class PayrollRunCreate(BaseModel): company_id:int=Field(gt=0); period:str=Field(min_length=4,max_length=20)
class PayrollResponse(BaseModel):
 model_config=ConfigDict(from_attributes=True); id:int; company_id:int; period:str; status:str; total_gross:Decimal; total_deductions:Decimal; total_net:Decimal
class BudgetCreate(BaseModel): company_id:int=Field(gt=0); name:str; fiscal_year:int=Field(gt=2000); notes:str|None=None
class BudgetLineCreate(BaseModel): account_id:int=Field(gt=0); period:int=Field(ge=1,le=12); amount:Decimal=Field(ge=0)
class BudgetResponse(BudgetCreate):
 model_config=ConfigDict(from_attributes=True); id:int; status:str
class ProjectCreate(BaseModel): company_id:int=Field(gt=0); code:str; name:str; customer_id:int|None=None; start_date:date|None=None; end_date:date|None=None; budget:Decimal=Field(default=0,ge=0); description:str|None=None
class ProjectResponse(ProjectCreate):
 model_config=ConfigDict(from_attributes=True); id:int; actual_cost:Decimal; status:str
class ContractCreate(BaseModel): company_id:int=Field(gt=0); project_id:int=Field(gt=0); contract_no:str; customer_id:int|None=None; contract_value:Decimal=Field(ge=0); start_date:date|None=None; end_date:date|None=None; retention_percent:Decimal=Field(default=0,ge=0,le=100); terms:str|None=None
class ContractResponse(ContractCreate):
 model_config=ConfigDict(from_attributes=True); id:int; status:str
