from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field

class ARAutoMatchRequest(BaseModel):
    company_id: int = Field(gt=0)
    partner_id: int = Field(gt=0)
    payment_id: int = Field(gt=0)
    as_of: date | None = None

class ARAllocationItem(BaseModel):
    document_id: int = Field(gt=0)
    amount: Decimal = Field(gt=0)

class ARAllocateRequest(BaseModel):
    company_id: int = Field(gt=0)
    payment_id: int = Field(gt=0)
    allocations: list[ARAllocationItem] = Field(min_length=1)

class ARWriteOffRequest(BaseModel):
    company_id: int = Field(gt=0)
    document_id: int = Field(gt=0)
    amount: Decimal = Field(gt=0)
    reason: str = Field(min_length=3, max_length=1000)
    writeoff_account_id: int = Field(gt=0)
    journal_id: int = Field(gt=0)

class ARWriteOffDecision(BaseModel):
    company_id: int = Field(gt=0)
    approve: bool
    reason: str | None = None

class ARReconcileRequest(BaseModel):
    company_id: int = Field(gt=0)
    partner_id: int | None = Field(default=None, gt=0)
    as_of: date | None = None
    persist: bool = True

class ARAdvanceReceiptRequest(BaseModel):
    company_id: int = Field(gt=0)
    partner_id: int = Field(gt=0)
    payment_date: date
    amount: Decimal = Field(gt=0)
    method: str = Field(min_length=1, max_length=30)
    reference: str | None = None
    notes: str | None = None
    idempotency_key: str | None = None
