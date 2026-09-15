from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class CommissionRuleCreate(BaseModel):
    company_id: int = Field(gt=0)
    code: str = Field(min_length=1, max_length=60)
    name: str = Field(min_length=1, max_length=200)
    basis: str = "net_sales"
    rate_percent: Decimal = Field(default=0, ge=0, le=100)
    fixed_amount: Decimal = Field(default=0, ge=0)
    min_base: Decimal = Field(default=0, ge=0)
    max_base: Decimal | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_range(self):
        if self.max_base is not None and self.max_base < self.min_base:
            raise ValueError("max_base cannot be less than min_base")
        if self.rate_percent == 0 and self.fixed_amount == 0:
            raise ValueError("Commission rule must define a percentage or fixed amount")
        if self.basis not in {"gross_sales", "net_sales", "gross_profit", "collection"}:
            raise ValueError("Unsupported commission basis")
        return self


class CommissionRuleResponse(CommissionRuleCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_active: bool


class CommissionCalculateRequest(BaseModel):
    employee_id: int = Field(gt=0)
    rule_id: int = Field(gt=0)
    period: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    source_type: str = Field(min_length=1, max_length=50)
    source_id: int | None = Field(default=None, gt=0)
    base_amount: Decimal = Field(ge=0)
    notes: str | None = None


class CommissionSettlementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
    employee_id: int
    rule_id: int
    period: str
    source_type: str
    source_id: int | None
    base_amount: Decimal
    commission_amount: Decimal
    status: str
    notes: str | None
