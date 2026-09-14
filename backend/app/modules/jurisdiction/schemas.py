from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class JurisdictionCreate(BaseModel):
    code: str = Field(min_length=2, max_length=20)
    country_code: str = Field(min_length=2, max_length=2)
    name: str = Field(min_length=1, max_length=150)
    default_currency: str = Field(min_length=3, max_length=3)
    timezone: str | None = None


class CompanyJurisdictionCreate(BaseModel):
    company_id: int = Field(gt=0)
    jurisdiction_id: int = Field(gt=0)
    role: str = "primary"
    effective_from: date
    effective_to: date | None = None
    tax_resident: bool = True
    vat_registered: bool = False
    tax_ids: dict = Field(default_factory=dict)


class PartnerJurisdictionCreate(BaseModel):
    partner_id: int = Field(gt=0)
    jurisdiction_id: int = Field(gt=0)
    role: str = "residence"
    effective_from: date
    effective_to: date | None = None
    tax_resident: bool = True
    vat_registered: bool = False
    tax_ids: dict = Field(default_factory=dict)


class TaxRuleCreate(BaseModel):
    jurisdiction_id: int = Field(gt=0)
    code: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=200)
    tax_type: str
    transaction_type: str
    taxpayer_type: str = "both"
    place_of_supply: str = "local"
    rate: Decimal = Field(default=Decimal("0"), ge=0)
    priority: int = 100
    conditions: dict = Field(default_factory=dict)
    effective_from: date
    effective_to: date | None = None
    source_reference: str | None = None
    version: str = "1"


class JurisdictionResolveRequest(BaseModel):
    company_id: int = Field(gt=0)
    partner_id: int | None = Field(default=None, gt=0)
    transaction_type: str
    transaction_date: date
    place_of_supply: str | None = None
    b2b: bool = True
    goods_or_services: str | None = None
    import_export: str | None = None


class JurisdictionDecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    jurisdiction_id: int
    transaction_type: str
    transaction_date: date
    place_of_supply: str
    b2b: bool
    rationale: dict
    rule_ids: list[int]
