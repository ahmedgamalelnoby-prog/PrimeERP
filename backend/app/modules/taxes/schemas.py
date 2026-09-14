"""Pydantic contracts for the canonical tax domain."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .constants import CUSTOM_TAX_TYPE, MAX_TAX_RATE, MIN_TAX_RATE, TAX_TYPES, VAT_TAX_TYPE, WHT_TAX_TYPE


class TaxRateBase(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=150)
    rate: Decimal = Field(ge=MIN_TAX_RATE, le=MAX_TAX_RATE)
    tax_type: str = Field(default=VAT_TAX_TYPE, max_length=20)
    is_withholding: bool = False

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("tax_type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        value = value.strip().lower()
        if value not in TAX_TYPES:
            raise ValueError(f"tax_type must be one of: {', '.join(sorted(TAX_TYPES))}")
        return value

    def model_post_init(self, __context) -> None:
        if self.tax_type == WHT_TAX_TYPE and not self.is_withholding:
            raise ValueError("WHT tax types must be marked as withholding")
        if self.is_withholding and self.tax_type != WHT_TAX_TYPE:
            raise ValueError("Withholding taxes must use tax_type=wht")


class TaxRateCreate(TaxRateBase):
    company_id: int = Field(gt=0)


class TaxRateUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str | None = Field(default=None, min_length=1, max_length=50)
    name: str | None = Field(default=None, min_length=1, max_length=150)
    rate: Decimal | None = Field(default=None, ge=MIN_TAX_RATE, le=MAX_TAX_RATE)
    tax_type: str | None = Field(default=None, max_length=20)
    is_withholding: bool | None = None
    is_active: bool | None = None


class TaxCalculationRequest(BaseModel):
    company_id: int = Field(gt=0)
    amount: Decimal = Field(ge=0)
    tax_ids: list[int] = Field(default_factory=list)
    inclusive: bool = False


__all__ = [
    "TaxRateBase", "TaxRateCreate", "TaxRateUpdate", "TaxCalculationRequest",
    "VAT_TAX_TYPE", "WHT_TAX_TYPE", "CUSTOM_TAX_TYPE",
]
