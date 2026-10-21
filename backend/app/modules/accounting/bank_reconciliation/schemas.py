from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field

class BankAccountCreate(BaseModel):
    company_id: int = Field(gt=0)
    code: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=120)
    currency_code: str = Field(default="EGP", min_length=3, max_length=3)
    opening_balance: Decimal = Decimal("0")

class BankAccountResponse(BankAccountCreate):
    id: int
    is_active: bool
    model_config = {"from_attributes": True}

class StatementLineCreate(BaseModel):
    company_id: int = Field(gt=0)
    bank_account_id: int = Field(gt=0)
    statement_date: date
    value_date: date | None = None
    reference: str | None = None
    description: str | None = None
    amount: Decimal
    direction: str

class StatementLineResponse(StatementLineCreate):
    id: int
    status: str
    matched_payment_id: int | None
    model_config = {"from_attributes": True}
