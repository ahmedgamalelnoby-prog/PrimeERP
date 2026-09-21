from pydantic import BaseModel, ConfigDict, Field
class BranchBase(BaseModel):
    company_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=150)
    code: str | None = Field(default=None, max_length=30)
    address: str | None = None
    phone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=150)
    is_active: bool = True
class BranchCreate(BranchBase): pass
class BranchUpdate(BaseModel):
    company_id: int | None = Field(default=None, gt=0)
    name: str | None = Field(default=None, min_length=1, max_length=150)
    code: str | None = Field(default=None, max_length=30)
    address: str | None = None
    phone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=150)
    is_active: bool | None = None
class BranchRead(BranchBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tenant_id: int
