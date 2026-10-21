from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class LocationCreate(BaseModel):
    company_id: int = Field(gt=0)
    warehouse_id: int = Field(gt=0)
    parent_id: Optional[int] = Field(default=None, gt=0)
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=150)
    location_type: str = Field(default="storage", max_length=30)
    is_virtual: bool = False
    description: Optional[str] = None


class LocationUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    location_type: Optional[str] = Field(default=None, max_length=30)
    is_virtual: Optional[bool] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None


class LocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    warehouse_id: int
    parent_id: Optional[int]
    code: str
    name: str
    location_type: str
    is_virtual: bool
    is_active: bool
    description: Optional[str]
