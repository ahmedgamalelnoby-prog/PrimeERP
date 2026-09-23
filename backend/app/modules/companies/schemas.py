from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CompanyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    code: str | None = Field(default=None, min_length=1, max_length=30)
    description: str | None = None
    address: str | None = None
    phone: str | None = Field(default=None, max_length=30)
    email: EmailStr | None = None
    tax_id: str | None = Field(default=None, max_length=100)
    legal_name: str | None = Field(default=None, max_length=200)
    commercial_registration_number: str | None = Field(default=None, max_length=100)
    tax_authority: str | None = Field(default=None, max_length=150)
    eta_registration_status: str = Field(default="not_configured", max_length=30)
    eta_taxpayer_id: str | None = Field(default=None, max_length=100)
    eta_last_verified_at: datetime | None = None
    is_active: bool = True


class CompanyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    code: str | None = Field(default=None, min_length=1, max_length=30)
    description: str | None = None
    address: str | None = None
    phone: str | None = Field(default=None, max_length=30)
    email: EmailStr | None = None
    tax_id: str | None = Field(default=None, max_length=100)
    legal_name: str | None = Field(default=None, max_length=200)
    commercial_registration_number: str | None = Field(default=None, max_length=100)
    tax_authority: str | None = Field(default=None, max_length=150)
    eta_registration_status: str | None = Field(default=None, max_length=30)
    eta_taxpayer_id: str | None = Field(default=None, max_length=100)
    eta_last_verified_at: datetime | None = None
    is_active: bool | None = None


class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tenant_id: int
    name: str
    code: str | None
    description: str | None
    address: str | None
    phone: str | None
    email: str | None
    tax_id: str | None
    legal_name: str | None
    commercial_registration_number: str | None
    tax_authority: str | None
    eta_registration_status: str
    eta_taxpayer_id: str | None
    eta_last_verified_at: datetime | None
    is_active: bool
