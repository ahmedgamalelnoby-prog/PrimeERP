from pydantic import BaseModel, ConfigDict, Field

class CustomerBase(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    customer_type: str = Field(default="customer", max_length=30)
    phone: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=150)
    tax_id: str | None = Field(default=None, max_length=100)
    address: str | None = None
    credit_limit: int = Field(default=0, ge=0)
    is_active: bool = True
class CustomerCreate(CustomerBase): pass
class CustomerUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=50)
    name: str | None = Field(default=None, min_length=1, max_length=200)
    customer_type: str | None = Field(default=None, max_length=30)
    phone: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=150)
    tax_id: str | None = Field(default=None, max_length=100)
    address: str | None = None
    credit_limit: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
class CustomerRead(CustomerBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tenant_id: int
