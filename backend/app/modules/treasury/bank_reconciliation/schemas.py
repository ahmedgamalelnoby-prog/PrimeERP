from datetime import date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

class BankAccountCreate(BaseModel):
    company_id: int = Field(gt=0)
    account_combination_id: int | None = Field(default=None, gt=0)
    name: str = Field(min_length=1, max_length=150)
    bank_name: str = Field(min_length=1, max_length=150)
    account_number: str | None = Field(default=None, max_length=100)
    currency: str = Field(default="EGP", max_length=10)
    opening_balance: Decimal = Field(default=Decimal("0"), ge=0)

class BankAccountResponse(BankAccountCreate):
    id: int
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

class BankStatementCreate(BaseModel):
    company_id: int = Field(gt=0)
    bank_account_id: int = Field(gt=0)
    statement_number: str = Field(min_length=1, max_length=100)
    period_start: date
    period_end: date
    opening_balance: Decimal
    closing_balance: Decimal

class BankStatementResponse(BankStatementCreate):
    id: int
    status: str
    model_config = ConfigDict(from_attributes=True)

class BankStatementLineCreate(BaseModel):
    external_id: str | None = Field(default=None, max_length=160)
    transaction_date: date
    value_date: date | None = None
    description: str | None = None
    reference: str | None = Field(default=None, max_length=150)
    cheque_number: str | None = Field(default=None, max_length=100)
    debit: Decimal = Field(default=Decimal("0"), ge=0)
    credit: Decimal = Field(default=Decimal("0"), ge=0)
    currency: str = Field(default="EGP", max_length=10)

class BankStatementLineResponse(BankStatementLineCreate):
    id: int
    fingerprint: str
    matched_amount: Decimal
    status: str
    model_config = ConfigDict(from_attributes=True)

class ReconciliationCreate(BaseModel):
    company_id: int = Field(gt=0)
    bank_account_id: int = Field(gt=0)
    statement_id: int = Field(gt=0)
    book_balance: Decimal

class ReconciliationResponse(ReconciliationCreate):
    id: int
    bank_balance: Decimal
    difference: Decimal
    status: str
    closed_by: int | None
    closed_at: object | None
    model_config = ConfigDict(from_attributes=True)

class MatchCreate(BaseModel):
    company_id: int = Field(gt=0)
    statement_line_id: int = Field(gt=0)
    source_type: str = Field(pattern="^(payment|cheque)$")
    source_id: int = Field(gt=0)
    amount: Decimal = Field(gt=0)

class MatchResponse(BaseModel):
    id: int
    statement_line_id: int
    source_type: str
    source_id: int
    amount: Decimal
    model_config = ConfigDict(from_attributes=True)

class AutoMatchResponse(BaseModel):
    matched: int
    candidates: int
