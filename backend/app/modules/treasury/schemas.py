from datetime import date
from decimal import Decimal
from pydantic import BaseModel,Field
class TreasuryAccountCreate(BaseModel):
    company_id:int=Field(gt=0); branch_id:int=Field(gt=0); code:str=Field(min_length=1,max_length=50); name:str=Field(min_length=2,max_length=150); account_type:str="cash"
class TreasuryTransactionCreate(BaseModel):
    treasury_account_id:int=Field(gt=0); transaction_type:str=Field(min_length=2,max_length=30); direction:str; amount:Decimal=Field(gt=0); transaction_date:date; reference:str|None=None; description:str|None=None
class TransferCreate(BaseModel):
    from_account_id:int=Field(gt=0); to_account_id:int=Field(gt=0); amount:Decimal=Field(gt=0); transfer_date:date; reference:str|None=None
class ChequeCreate(BaseModel):
    treasury_account_id:int=Field(gt=0); cheque_number:str=Field(min_length=1,max_length=100); cheque_type:str; amount:Decimal=Field(gt=0); due_date:date; reference:str|None=None
class AllocationCreate(BaseModel):
    treasury_transaction_id:int=Field(gt=0); document_type:str=Field(min_length=2,max_length=40); document_id:int=Field(gt=0); amount:Decimal=Field(gt=0)
