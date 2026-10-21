from decimal import Decimal
from pydantic import BaseModel, Field

class QuotationLineCreate(BaseModel):
    item_id: int = Field(gt=0)
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    discount_amount: Decimal = Field(default=Decimal("0"), ge=0)

class QuotationLineResponse(QuotationLineCreate):
    id: int
    line_total: Decimal
    class Config:
        from_attributes = True

class QuotationCreate(BaseModel):
    company_id: int = Field(gt=0)
    customer_id: int = Field(gt=0)
    quotation_number: str = Field(min_length=1, max_length=50)
    quotation_date: str = Field(min_length=8, max_length=20)
    valid_until: str | None = Field(default=None, max_length=20)
    notes: str | None = None
    lines: list[QuotationLineCreate] = Field(min_length=1)

class QuotationResponse(BaseModel):
    id: int
    company_id: int
    customer_id: int
    quotation_number: str
    quotation_date: str
    valid_until: str | None
    status: str
    total_amount: Decimal
    notes: str | None
    lines: list[QuotationLineResponse]
    class Config:
        from_attributes = True
