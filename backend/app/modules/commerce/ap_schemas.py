from datetime import date
from decimal import Decimal
from pydantic import BaseModel,Field
class APAllocateItem(BaseModel): document_id:int=Field(gt=0); amount:Decimal=Field(gt=0)
class APAllocateRequest(BaseModel): company_id:int=Field(gt=0); payment_id:int=Field(gt=0); allocations:list[APAllocateItem]=Field(min_length=1)
class APAdvancePaymentRequest(BaseModel): company_id:int=Field(gt=0); partner_id:int=Field(gt=0); payment_date:date; amount:Decimal=Field(gt=0); method:str=Field(min_length=1,max_length=30); reference:str|None=None; notes:str|None=None; idempotency_key:str|None=None
class APWriteOffRequest(BaseModel): company_id:int=Field(gt=0); document_id:int=Field(gt=0); amount:Decimal=Field(gt=0); reason:str=Field(min_length=3,max_length=1000); writeoff_account_id:int=Field(gt=0); journal_id:int=Field(gt=0)
class APWriteOffDecision(BaseModel): company_id:int=Field(gt=0); approve:bool; reason:str|None=None
class APMatchRequest(BaseModel): company_id:int=Field(gt=0); payment_id:int=Field(gt=0); partner_id:int=Field(gt=0); as_of:date|None=None
class APReconcileRequest(BaseModel): company_id:int=Field(gt=0); partner_id:int|None=None; as_of:date|None=None; persist:bool=True
class APVarianceDecision(BaseModel): company_id:int=Field(gt=0); approve:bool=False; waive:bool=False; reason:str|None=None
class APVarianceCreateRequest(BaseModel): company_id:int=Field(gt=0); bill_id:int=Field(gt=0); variance_type:str=Field(min_length=2,max_length=30); expected_amount:Decimal; actual_amount:Decimal; tolerance:Decimal=Field(default=0,ge=0); reason:str|None=None
