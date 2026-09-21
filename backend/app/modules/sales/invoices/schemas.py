from datetime import date,datetime
from decimal import Decimal
from pydantic import BaseModel,Field,ConfigDict
class InvoiceCreate(BaseModel): sales_order_id:int=Field(gt=0);invoice_date:date;currency_code:str=Field(default="EGP",min_length=3,max_length=3)
class InvoiceResponse(BaseModel):
 id:int;tenant_id:int;company_id:int;branch_id:int;customer_id:int;sales_order_id:int|None;invoice_number:str;invoice_date:date;status:str;currency_code:str;subtotal:Decimal;tax_total:Decimal;discount_total:Decimal;grand_total:Decimal;journal_entry_id:int|None;created_by:int|None;created_at:datetime;updated_at:datetime
 model_config=ConfigDict(from_attributes=True)
class InvoicePost(BaseModel):
 fiscal_year_id:int=Field(gt=0);period_id:int=Field(gt=0);journal_id:int=Field(gt=0);receivable_account_id:int=Field(gt=0);revenue_account_id:int=Field(gt=0);tax_account_id:int|None=Field(default=None,gt=0)
