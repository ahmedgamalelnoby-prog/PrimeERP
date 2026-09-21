from pydantic import BaseModel, ConfigDict, Field

class CompanyBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    code: str | None = Field(default=None, max_length=30)
    description: str | None = None
    address: str | None = None
    phone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=150)
    tax_id: str | None = Field(default=None, max_length=100)
    is_active: bool = True

class CompanyCreate(CompanyBase): pass

class CompanyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    code: str | None = Field(default=None, max_length=30)
    description: str | None = None
    address: str | None = None
    phone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=150)
    tax_id: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None

class CompanyRead(CompanyBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tenant_id: int
