from datetime import date
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

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
    variant_id: int | None = Field(default=None, gt=0)
    tax_rate_id: int | None = Field(default=None, gt=0)
    tax_rate_ids: list[int] | None = None
    description: str | None = None
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    discount_percent: Decimal = Field(default=0, ge=0, le=100)
    tax_percent: Decimal = Field(default=0, ge=0, le=100)

    @model_validator(mode="after")
    def validate_tax_source(self):
        if self.tax_rate_ids is not None and len(self.tax_rate_ids) != len(set(self.tax_rate_ids)):
            raise ValueError("Duplicate tax ids are not allowed")
        if self.tax_rate_ids is not None and any(tax_id <= 0 for tax_id in self.tax_rate_ids):
            raise ValueError("Tax ids must be positive")
        if self.tax_rate_id is not None and self.tax_rate_ids is not None and self.tax_rate_id not in self.tax_rate_ids:
            raise ValueError("tax_rate_id must be included in tax_rate_ids when both are supplied")
        if self.tax_rate_id is not None and self.tax_rate_ids is None:
            self.tax_rate_ids = [self.tax_rate_id]
        if self.tax_rate_ids is not None and self.tax_percent != 0:
            raise ValueError("Do not send tax_percent when tax_rate_ids are provided; Tax Master is authoritative")
        if self.tax_rate_ids is None and self.tax_percent != 0:
            raise ValueError("Tax Master is required for non-zero tax rates")
        return self


class DocumentCreate(BaseModel):
    company_id: int = Field(gt=0)
    partner_id: int = Field(gt=0)
    document_type: SaleType | PurchaseType
    number: str = Field(min_length=1, max_length=60)
    document_date: date
    due_date: date | None = None
    warehouse_id: int | None = Field(default=None, gt=0)
    notes: str | None = None
    lines: list[DocumentLineCreate] = Field(min_length=1)
    receipt_ids: list[int] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_receipt_links(self):
        if len(self.receipt_ids) != len(set(self.receipt_ids)):
            raise ValueError("Duplicate receipt ids are not allowed")
        if any(receipt_id <= 0 for receipt_id in self.receipt_ids):
            raise ValueError("Receipt ids must be positive")
        if self.receipt_ids and self.document_type != "bill":
            raise ValueError("receipt_ids are allowed only for purchase bills")
        return self


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
    partner_id: int
    document_type: str
    number: str
    document_date: date
    due_date: date | None
    status: str
    warehouse_id: int | None
    subtotal: Decimal
    tax_total: Decimal
    discount_total: Decimal
    paid_total: Decimal
    total: Decimal
 

class PaymentAllocationCreate(BaseModel):
    document_id: int = Field(gt=0)
    amount: Decimal = Field(gt=0)


class PaymentCreate(BaseModel):
    company_id: int = Field(gt=0)
    document_id: int = Field(gt=0)
    payment_date: date
    amount: Decimal = Field(gt=0)
    wht_amount: Decimal = Field(default=0, ge=0)
    auto_wht: bool = True
    method: str = Field(min_length=1, max_length=30)
    reference: str | None = None
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=100)
    notes: str | None = None
    cheque_number: str | None = Field(default=None, min_length=1, max_length=100)
    cheque_bank_name: str | None = Field(default=None, max_length=150)
    cheque_account_number: str | None = Field(default=None, max_length=100)
    cheque_due_date: date | None = None
    allocations: list[PaymentAllocationCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_wht(self):
        if self.wht_amount > self.amount:
            raise ValueError("WHT amount cannot exceed payment amount")
        if self.allocations:
            ids = [a.document_id for a in self.allocations]
            if len(ids) != len(set(ids)):
                raise ValueError("Duplicate payment allocation documents are not allowed")
            total = sum((a.amount for a in self.allocations), Decimal("0"))
            if total != self.amount:
                raise ValueError("Payment allocations total must equal the payment amount")
        return self


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
    document_kind: str
    document_id: int | None
    payment_date: date
    amount: Decimal
    wht_amount: Decimal
    method: str
    reference: str | None
    notes: str | None
    status: str
    reversed_of_id: int | None


class PaymentReverse(BaseModel):
    company_id: int = Field(gt=0)
    reversal_date: date
    notes: str | None = None


class AgingRow(BaseModel):
    direction: str
    document_id: int
    document_number: str
    partner_id: int
    document_date: date
    due_date: date
    total: Decimal
    paid_total: Decimal
    outstanding: Decimal
    days_overdue: int
    bucket: str

class AgingSummary(BaseModel):
    as_of: date
    receivable: Decimal
    payable: Decimal
    net: Decimal
    rows: list[AgingRow]


class StatementRow(BaseModel):
    date: date
    document_type: str
    document_id: int | None
    reference: str
    debit: Decimal
    credit: Decimal
    balance: Decimal


class PartnerStatement(BaseModel):
    company_id: int
    partner_id: int
    direction: Literal["customer", "vendor"]
    from_date: date | None
    to_date: date | None
    as_of: date
    opening_balance: Decimal
    closing_balance: Decimal
    rows: list[StatementRow]
