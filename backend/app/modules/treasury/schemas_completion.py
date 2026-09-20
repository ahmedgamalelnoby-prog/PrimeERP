from datetime import date
from decimal import Decimal
from pydantic import BaseModel,Field,ConfigDict
class TreasuryTransactionCreate(BaseModel):
 company_id:int=Field(gt=0); branch_id:int|None=Field(default=None,gt=0); transaction_date:date; transaction_type:str=Field(pattern="^(receipt|payment|transfer|deposit|withdrawal)$"); account_id:int=Field(gt=0); offset_account_id:int=Field(gt=0); amount:Decimal=Field(gt=0); currency:str="EGP"; reference:str|None=None; description:str|None=None; requires_approval:bool=False
class TreasuryApproval(BaseModel): approve:bool; reason:str|None=None
class TreasuryDailyCloseCreate(BaseModel): company_id:int=Field(gt=0); branch_id:int|None=Field(default=None,gt=0); closing_date:date; counted_balance:Decimal=Field(ge=0); notes:str|None=None
class TreasuryForecastCreate(BaseModel): company_id:int=Field(gt=0); forecast_date:date; expected_inflow:Decimal=Field(ge=0); expected_outflow:Decimal=Field(ge=0); opening_balance:Decimal=Field(ge=0); source:str="manual"
class TreasuryTransactionResponse(BaseModel):
 model_config=ConfigDict(from_attributes=True)
 id:int; company_id:int; branch_id:int|None; transaction_date:date; transaction_type:str; account_id:int; offset_account_id:int; amount:Decimal; currency:str; reference:str|None; description:str|None; status:str; approval_status:str; journal_entry_id:int|None

class TreasuryTransactionListResponse(TreasuryTransactionResponse):
    pass
