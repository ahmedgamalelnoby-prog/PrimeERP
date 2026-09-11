from datetime import date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class ChequeCreate(BaseModel):
    company_id: int = Field(gt=0)
    partner_id: int | None = Field(default=None, gt=0)
    direction: str = "received"
    cheque_number: str = Field(min_length=1, max_length=100)
    bank_name: str | None = Field(default=None, max_length=150)
    account_number: str | None = Field(default=None, max_length=100)
    cheque_date: date
    due_date: date
    amount: Decimal = Field(gt=0)
    currency: str = Field(default="EGP", min_length=3, max_length=10)
    notes: str | None = None


class ChequeAction(BaseModel):
    company_id: int = Field(gt=0)
    event_date: date | None = None
    reference: str | None = Field(default=None, max_length=150)
    notes: str | None = None


class ChequeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
    partner_id: int | None
    direction: str
    cheque_number: str
    bank_name: str | None
    account_number: str | None
    cheque_date: date
    due_date: date
    amount: Decimal
    currency: str
    status: str
    source_payment_id: int | None
    original_cheque_id: int | None
    notes: str | None


class ChequeEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    cheque_id: int
    event_type: str
    from_status: str | None
    to_status: str
    event_date: date
    reference: str | None
    notes: str | None
    created_by: int | None
