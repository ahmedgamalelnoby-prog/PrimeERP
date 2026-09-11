from datetime import date
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

PartnerType = Literal["customer", "vendor", "both"]
SaleType = Literal["quotation", "order", "delivery", "invoice", "credit_note"]
PurchaseType = Literal["requisition", "rfq", "order", "receipt", "bill", "debit_note"]


class PartnerCreate(BaseModel):
    company_id: int = Field(gt=0)
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    partner_type: PartnerType = "customer"
    tax_number: str | None = None
    phone: str | None = None
    email: str | None = None
    credit_limit: Decimal = Field(default=0, ge=0)
    payment_terms_days: int = Field(default=0, ge=0)


class PartnerResponse(PartnerCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_active: bool


class DocumentLineCreate(BaseModel):
    item_id: int = Field(gt=0)
    tax_rate_id: int | None = Field(default=None, gt=0)
    description: str | None = None
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    discount_percent: Decimal = Field(default=0, ge=0, le=100)
    tax_percent: Decimal = Field(default=0, ge=0, le=100)


class DocumentCreate(BaseModel):
    company_id: int = Field(gt=0)
    partner_id: int = Field(gt=0)
    document_type: SaleType | PurchaseType
    number: str = Field(min_length=1, max_length=60)
    document_date: date
    warehouse_id: int | None = Field(default=None, gt=0)
    notes: str | None = None
    lines: list[DocumentLineCreate] = Field(min_length=1)


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
    partner_id: int
    document_type: str
    number: str
    document_date: date
    status: str
    warehouse_id: int | None
    subtotal: Decimal
    tax_total: Decimal
    discount_total: Decimal
    total: Decimal
    paid_total: Decimal


class PaymentCreate(BaseModel):
    company_id: int = Field(gt=0)
    document_id: int = Field(gt=0)
    payment_date: date
    amount: Decimal = Field(gt=0)
    method: str = Field(min_length=1, max_length=30)
    reference: str | None = None
    notes: str | None = None


class PaymentReverse(BaseModel):
    company_id: int = Field(gt=0)
    reversal_date: date
    notes: str | None = None
