from datetime import datetime\nfrom pydantic import BaseModel, ConfigDict, EmailStr, Field


class CompanyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    code: str | None = Field(default=None, min_length=1, max_length=30)
    description: str | None = None
    address: str | None = None
    phone: str | None = Field(default=None, max_length=30)
    email: EmailStr | None = None
    tax_id: str | None = Field(default=None, max_length=100)
    is_active: bool = True


class CompanyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    code: str | None = Field(default=None, min_length=1, max_length=30)
    description: str | None = None
    address: str | None = None
    phone: str | None = Field(default=None, max_length=30)
    email: EmailStr | None = None
    tax_id: str | None = Field(default=None, max_length=100)
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
    is_active: bool
