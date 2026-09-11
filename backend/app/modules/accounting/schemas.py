from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


TaxType = Literal["vat", "wht", "custom"]


class TaxRateBase(BaseModel):
    code: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=120)
    rate: Decimal = Field(ge=0, le=100)
    tax_type: TaxType = "vat"
    is_withholding: bool = False

    @model_validator(mode="after")
    def validate_withholding(self):
        if self.tax_type == "wht" and not self.is_withholding:
            raise ValueError("WHT tax types must be marked as withholding")
        if self.is_withholding and self.tax_type != "wht":
            raise ValueError("Withholding taxes must use tax_type=wht")
        return self


class TaxRateCreate(TaxRateBase):
    company_id: int = Field(gt=0)


class TaxRateUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=40)
    name: str | None = Field(default=None, min_length=1, max_length=120)
    rate: Decimal | None = Field(default=None, ge=0, le=100)
    tax_type: TaxType | None = None
    is_withholding: bool | None = None
    is_active: bool | None = None


class TaxRateResponse(TaxRateBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
    is_active: bool
