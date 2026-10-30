from pydantic import BaseModel, ConfigDict, EmailStr, Field


class BranchCreate(BaseModel):
    company_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=150)
    code: str | None = Field(default=None, min_length=1, max_length=30)
    address: str | None = None
    phone: str | None = Field(default=None, max_length=30)
    email: EmailStr | None = None
    is_active: bool = True


class BranchUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    code: str | None = Field(default=None, min_length=1, max_length=30)
    address: str | None = None
    phone: str | None = Field(default=None, max_length=30)
    email: EmailStr | None = None
    is_active: bool | None = None


class BranchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tenant_id: int
    company_id: int
    name: str
    code: str | None
    address: str | None
    phone: str | None
    email: str | None
    is_active: bool


class BranchMemberCreate(BaseModel):
    user_id: int = Field(gt=0)


class BranchMemberResponse(BaseModel):
    user_id: int
    username: str
    full_name: str | None
    is_active: bool
    assigned_by_user_id: int | None
