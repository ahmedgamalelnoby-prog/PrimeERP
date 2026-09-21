from datetime import date
from decimal import Decimal
from pydantic import BaseModel,Field
class CarrierCreate(BaseModel):
 code:str=Field(min_length=1,max_length=50)
 name:str=Field(min_length=1,max_length=150)
class CarrierRuleCreate(BaseModel):
 carrier_id:int
 rule_type:str=Field(min_length=2,max_length=30)
 fixed_amount:Decimal=0
 rate_percent:Decimal=0
 amount_per_kg:Decimal=0
 amount_per_item:Decimal=0
 zone:str|None=None
 cod_fee:Decimal=0
 visa_withdrawal_fee:Decimal=0
 priority:int=100
class ShipmentItemCreate(BaseModel):
 product_id:int
 quantity:Decimal=Field(gt=0)
class ShipmentCreate(BaseModel):
 company_id:int
 branch_id:int
 sales_order_id:int|None=None
 carrier_id:int|None=None
 payment_method:str|None=None
 cod_amount:Decimal=Field(default=0,ge=0)
 shipping_charge:Decimal=Field(default=0,ge=0)
 carrier_charge:Decimal=Field(default=0,ge=0)
 customer_amount:Decimal=Field(default=0,ge=0)
 lines:list[ShipmentItemCreate]=Field(min_length=1)
 notes:str|None=None
class StatusChange(BaseModel):
 status:str
class ReturnCreate(BaseModel):
 reason:str|None=None
class SettlementCreate(BaseModel):
 company_id:int
 branch_id:int
 carrier_id:int
 settlement_date:date
 orders_amount:Decimal=Field(default=0,ge=0)
 carrier_charges:Decimal=Field(default=0,ge=0)
 cod_collected:Decimal=Field(default=0,ge=0)
