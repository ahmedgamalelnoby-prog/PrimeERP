from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class WarehouseCreate(BaseModel):
    tenant_id: int = Field(gt=0)
    company_id: int = Field(gt=0)
    branch_id: Optional[int] = Field(default=None, gt=0)
    code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=150)
    description: Optional[str] = None
    is_central: bool = False


class WarehouseUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class WarehouseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    company_id: int
    branch_id: Optional[int]
    code: str
    name: str
    description: Optional[str]
    is_central: bool
    is_active: bool
