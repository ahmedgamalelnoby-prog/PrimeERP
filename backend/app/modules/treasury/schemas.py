from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field


class PaymentMethodCreate(BaseModel):
    company_id: int = Field(gt=0)
    code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=120)
    method_type: str = Field(min_length=1, max_length=30)
    is_incoming: bool = True
    is_outgoing: bool = True


class PaymentMethodResponse(PaymentMethodCreate):
    id: int
    is_active: bool
    model_config = {"from_attributes": True}


class PaymentCreate(BaseModel):
    company_id: int = Field(gt=0)
    branch_id: int | None = Field(default=None, gt=0)
    payment_method_id: int = Field(gt=0)
    party_type: str
    party_id: int = Field(gt=0)
    direction: str
    payment_date: date
    amount: Decimal = Field(gt=0)
    currency_code: str = Field(default="EGP", min_length=3, max_length=3)
    reference: str | None = Field(default=None, max_length=120)
    source_module: str | None = Field(default=None, max_length=80)
    source_entity: str | None = Field(default=None, max_length=80)
    source_id: str | None = Field(default=None, max_length=80)
    notes: str | None = None


class PaymentResponse(PaymentCreate):
    id: int
    status: str
    reversed_payment_id: int | None
    model_config = {"from_attributes": True}


class PaymentReverseRequest(BaseModel):
    notes: str | None = None
