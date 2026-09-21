from datetime import date,datetime
from decimal import Decimal
from pydantic import BaseModel,ConfigDict,Field
class SupplierCreate(BaseModel):
    code:str=Field(min_length=1,max_length=80); name:str=Field(min_length=2,max_length=200); phone:str|None=None; email:str|None=None; tax_id:str|None=None; address:str|None=None; credit_limit:Decimal=Field(default=0,ge=0)
class SupplierResponse(SupplierCreate):
    id:int; tenant_id:int; is_active:bool; created_at:datetime; updated_at:datetime
    model_config=ConfigDict(from_attributes=True)
class PurchaseOrderLineCreate(BaseModel):
    product_id:int=Field(gt=0); quantity:Decimal=Field(gt=0); unit_price:Decimal=Field(ge=0); discount:Decimal=Field(default=0,ge=0); tax_rate:Decimal=Field(default=0,ge=0)
class PurchaseOrderCreate(BaseModel):
    company_id:int=Field(gt=0); branch_id:int=Field(gt=0); supplier_id:int=Field(gt=0); order_date:date; lines:list[PurchaseOrderLineCreate]=Field(min_length=1); notes:str|None=None
class PurchaseOrderResponse(BaseModel):
    id:int; tenant_id:int; company_id:int; branch_id:int; supplier_id:int; order_number:str; order_date:date; status:str; subtotal:Decimal; discount:Decimal; tax:Decimal; grand_total:Decimal; notes:str|None; created_at:datetime; updated_at:datetime
    model_config=ConfigDict(from_attributes=True)
class ReceiptLine(BaseModel):
    product_id:int=Field(gt=0); location_id:int=Field(gt=0); quantity:Decimal=Field(gt=0)
class ReceiptCreate(BaseModel):
    purchase_order_id:int=Field(gt=0); warehouse_id:int=Field(gt=0); receipt_date:date; lines:list[ReceiptLine]=Field(min_length=1); notes:str|None=None
class ReceiptResponse(BaseModel):
    id:int; tenant_id:int; purchase_order_id:int; warehouse_id:int; receipt_number:str; receipt_date:date; status:str; notes:str|None
    model_config=ConfigDict(from_attributes=True)
class PurchaseInvoiceCreate(BaseModel):
    purchase_order_id:int=Field(gt=0); invoice_date:date
class PurchaseInvoicePost(BaseModel):
    journal_id:int=Field(gt=0); fiscal_year_id:int=Field(gt=0); period_id:int=Field(gt=0); inventory_account_id:int=Field(gt=0); payable_account_id:int=Field(gt=0); tax_account_id:int|None=Field(default=None,gt=0)
class PurchaseInvoiceResponse(BaseModel):
    id:int; tenant_id:int; company_id:int; branch_id:int; supplier_id:int; purchase_order_id:int|None; invoice_number:str; invoice_date:date; status:str; subtotal:Decimal; discount:Decimal; tax:Decimal; grand_total:Decimal; journal_entry_id:int|None
    model_config=ConfigDict(from_attributes=True)