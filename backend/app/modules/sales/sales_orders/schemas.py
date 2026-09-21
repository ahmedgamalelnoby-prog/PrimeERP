from datetime import date,datetime
from decimal import Decimal
from pydantic import BaseModel,Field,ConfigDict
class SalesOrderLineCreate(BaseModel):
 product_id:int=Field(gt=0);quantity:Decimal=Field(gt=0);unit_price:Decimal=Field(ge=0);discount:Decimal=Field(default=0,ge=0);tax_rate:Decimal=Field(default=0,ge=0)
class SalesOrderCreate(BaseModel):
 company_id:int=Field(gt=0);branch_id:int=Field(gt=0);customer_id:int=Field(gt=0);order_date:date;currency_code:str=Field(default="EGP",min_length=3,max_length=3);notes:str|None=None;lines:list[SalesOrderLineCreate]=Field(min_length=1)
class SalesOrderAction(BaseModel): reason:str|None=None
class SalesOrderLineResponse(SalesOrderLineCreate):
 id:int;line_total:Decimal
 model_config=ConfigDict(from_attributes=True)
class SalesOrderResponse(BaseModel):
 id:int;tenant_id:int;company_id:int;branch_id:int;customer_id:int;order_number:str;order_date:date;status:str;currency_code:str;subtotal:Decimal;tax_total:Decimal;discount_total:Decimal;grand_total:Decimal;notes:str|None=None;created_by:int|None=None;created_at:datetime;updated_at:datetime;lines:list[SalesOrderLineResponse]=[]
 model_config=ConfigDict(from_attributes=True)