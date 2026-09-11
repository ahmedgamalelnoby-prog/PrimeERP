from decimal import Decimal
from pydantic import BaseModel, Field


class SalesOrderCreate(BaseModel):
    company_id: int = Field(gt=0)
    customer_id: int = Field(gt=0)
    warehouse_id: int = Field(gt=0)
    order_number: str = Field(min_length=1, max_length=50)
    order_date: str = Field(min_length=8, max_length=20)
    total_amount: Decimal = Field(default=Decimal("0"), ge=0)
    reference: str | None = Field(default=None, max_length=100)
    notes: str | None = None


class SalesOrderUpdate(BaseModel):
    total_amount: Decimal | None = Field(default=None, ge=0)
    reference: str | None = Field(default=None, max_length=100)
    notes: str | None = None


class SalesOrderResponse(SalesOrderCreate):
    id: int
    status: str

    class Config:
        from_attributes = True
