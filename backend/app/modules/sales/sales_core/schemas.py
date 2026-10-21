from decimal import Decimal
from pydantic import BaseModel, Field


class SalesOrderLineCreate(BaseModel):
    item_id: int = Field(gt=0)
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    discount_amount: Decimal = Field(default=Decimal("0"), ge=0)


class SalesOrderLineResponse(SalesOrderLineCreate):
    id: int
    line_total: Decimal
    class Config:
        from_attributes = True


class SalesOrderCreate(BaseModel):
    company_id: int = Field(gt=0)
    customer_id: int = Field(gt=0)
    warehouse_id: int = Field(gt=0)
    order_number: str = Field(min_length=1, max_length=50)
    order_date: str = Field(min_length=8, max_length=20)
    reference: str | None = Field(default=None, max_length=100)
    notes: str | None = None
    lines: list[SalesOrderLineCreate] = Field(min_length=1)


class SalesOrderResponse(BaseModel):
    id: int
    company_id: int
    customer_id: int
    warehouse_id: int
    order_number: str
    order_date: str
    status: str
    total_amount: Decimal
    reference: str | None
    notes: str | None
    lines: list[SalesOrderLineResponse]
    class Config:
        from_attributes = True
