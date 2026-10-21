from decimal import Decimal
from pydantic import BaseModel,Field
class OutletCreate(BaseModel):
    company_id:int=Field(gt=0); branch_id:int=Field(gt=0); warehouse_id:int=Field(gt=0); code:str=Field(min_length=1,max_length=50); name:str=Field(min_length=2,max_length=150); outlet_type:str="restaurant"
class TerminalCreate(BaseModel):
    outlet_id:int=Field(gt=0); code:str=Field(min_length=1,max_length=50); name:str=Field(min_length=2,max_length=150)
class SessionCreate(BaseModel):
    terminal_id:int=Field(gt=0); opening_cash:Decimal=Field(default=0,ge=0)
class POSLine(BaseModel):
    product_id:int=Field(gt=0); quantity:Decimal=Field(gt=0); unit_price:Decimal=Field(ge=0)
class POSOrderCreate(BaseModel):
    outlet_id:int=Field(gt=0); terminal_id:int=Field(gt=0); session_id:int=Field(gt=0); lines:list[POSLine]=Field(min_length=1)
class POSPaymentCreate(BaseModel):
    payment_method:str=Field(min_length=2,max_length=30); amount:Decimal=Field(gt=0); reference:str|None=None
