from decimal import Decimal
from pydantic import BaseModel, Field
class OutletCreate(BaseModel):
    company_id:int=Field(gt=0); branch_id:int=Field(gt=0); inventory_location_id:int=Field(gt=0); code:str=Field(min_length=1,max_length=60); name:str=Field(min_length=1,max_length=200)
class DeviceCreate(BaseModel):
    company_id:int=Field(gt=0); outlet_id:int=Field(gt=0); code:str=Field(min_length=1,max_length=60); name:str=Field(min_length=1,max_length=160)
class SessionOpen(BaseModel):
    company_id:int=Field(gt=0); outlet_id:int=Field(gt=0); device_id:int=Field(gt=0); cashier_user_id:int=Field(gt=0)
class OrderLineCreate(BaseModel):
    item_id:int=Field(gt=0); variant_id:int|None=Field(default=None,gt=0); quantity:Decimal=Field(gt=0); unit_price:Decimal=Field(gt=0); tax_percent:Decimal=Field(default=0,ge=0,max=100)
class OrderCreate(BaseModel):
    company_id:int=Field(gt=0); session_id:int=Field(gt=0); number:str=Field(min_length=1,max_length=80); lines:list[OrderLineCreate]=Field(min_length=1)
class PaymentCreate(BaseModel):
    company_id:int=Field(gt=0); order_id:int=Field(gt=0); method:str; amount:Decimal=Field(gt=0); idempotency_key:str=Field(min_length=1,max_length=120)
class SessionClose(BaseModel):
    company_id:int=Field(gt=0)
    closing_total:Decimal=Field(ge=0)
    closing_cash:Decimal|None=Field(default=None,ge=0)
    closing_card:Decimal|None=Field(default=None,ge=0)
    closing_bank:Decimal|None=Field(default=None,ge=0)
    closing_other:Decimal|None=Field(default=None,ge=0)
