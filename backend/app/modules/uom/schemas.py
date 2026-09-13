from decimal import Decimal
from pydantic import BaseModel, Field


class UOMCreate(BaseModel):
    company_id: int = Field(gt=0)
    code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=100)
    category: str = Field(min_length=1, max_length=50)
    factor_to_base: Decimal = Field(default=Decimal("1"), gt=0)
    is_base: bool = False


class UOMUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    factor_to_base: Decimal | None = Field(default=None, gt=0)
    is_base: bool | None = None
    is_active: bool | None = None


class UOMResponse(UOMCreate):
    id: int
    is_active: bool
    model_config = {"from_attributes": True}
