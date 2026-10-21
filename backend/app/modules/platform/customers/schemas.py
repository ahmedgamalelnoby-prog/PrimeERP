from pydantic import BaseModel, Field
from decimal import Decimal


class CustomerCreate(BaseModel):
    company_id: int = Field(gt=0)
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    tax_id: str | None = Field(default=None, max_length=100)
    email: str | None = Field(default=None, max_length=200)
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = None
    credit_limit: Decimal = Field(default=Decimal("0"), ge=0)


class CustomerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    tax_id: str | None = Field(default=None, max_length=100)
    email: str | None = Field(default=None, max_length=200)
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = None
    credit_limit: Decimal | None = Field(default=None, ge=0)
    is_active: bool | None = None


class CustomerResponse(CustomerCreate):
    id: int
    is_active: bool

    class Config:
        from_attributes = True
