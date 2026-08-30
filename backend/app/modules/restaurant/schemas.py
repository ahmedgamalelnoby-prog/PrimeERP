from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


# =========================================================
# Floors
# =========================================================

class FloorBase(BaseModel):
    branch_id: int
    name: str = Field(min_length=2, max_length=100)
    code: Optional[str] = Field(default=None, max_length=30)
    description: Optional[str] = None
    display_order: int = 0
    is_active: bool = True


class FloorCreate(FloorBase):
    pass


class FloorUpdate(BaseModel):
    branch_id: Optional[int] = None
    name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100,
    )
    code: Optional[str] = Field(default=None, max_length=30)
    description: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class FloorResponse(FloorBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =========================================================
# Restaurant Tables
# =========================================================

class RestaurantTableBase(BaseModel):
    branch_id: int
    floor_id: int

    name: str = Field(
        min_length=1,
        max_length=100,
    )

    code: str = Field(
        min_length=1,
        max_length=30,
    )

    capacity: int = Field(default=4, ge=1, le=100)

    shape: str = "square"

    position_x: Decimal = Decimal("0")
    position_y: Decimal = Decimal("0")
    width: Decimal = Decimal("100")
    height: Decimal = Decimal("100")

    status: str = "available"
    is_active: bool = True


class RestaurantTableCreate(RestaurantTableBase):
    pass


class RestaurantTableUpdate(BaseModel):
    branch_id: Optional[int] = None
    floor_id: Optional[int] = None
    name: Optional[str] = Field(default=None, max_length=100)
    code: Optional[str] = Field(default=None, max_length=30)
    capacity: Optional[int] = Field(default=None, ge=1, le=100)
    shape: Optional[str] = None
    position_x: Optional[Decimal] = None
    position_y: Optional[Decimal] = None
    width: Optional[Decimal] = None
    height: Optional[Decimal] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None


class RestaurantTableResponse(RestaurantTableBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =========================================================
# Preparation Stations
# =========================================================

class PreparationStationBase(BaseModel):
    branch_id: int

    name: str = Field(
        min_length=2,
        max_length=100,
    )

    code: str = Field(
        min_length=1,
        max_length=30,
    )

    description: Optional[str] = None
    station_type: str = "kitchen"
    printer_name: Optional[str] = None
    display_order: int = 0
    is_kds_enabled: bool = True
    is_printer_enabled: bool = False
    is_active: bool = True


class PreparationStationCreate(PreparationStationBase):
    pass


class PreparationStationUpdate(BaseModel):
    branch_id: Optional[int] = None
    name: Optional[str] = Field(default=None, max_length=100)
    code: Optional[str] = Field(default=None, max_length=30)
    description: Optional[str] = None
    station_type: Optional[str] = None
    printer_name: Optional[str] = None
    display_order: Optional[int] = None
    is_kds_enabled: Optional[bool] = None
    is_printer_enabled: Optional[bool] = None
    is_active: Optional[bool] = None


class PreparationStationResponse(PreparationStationBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =========================================================
# Order Types
# =========================================================

class OrderTypeBase(BaseModel):
    branch_id: int

    name: str = Field(
        min_length=2,
        max_length=100,
    )

    code: str = Field(
        min_length=1,
        max_length=30,
    )

    order_category: str
    description: Optional[str] = None

    service_charge_percentage: Decimal = Decimal("0")
    minimum_order_amount: Decimal = Decimal("0")

    requires_table: bool = False
    requires_customer: bool = False
    requires_delivery_address: bool = False

    display_order: int = 0
    is_active: bool = True


class OrderTypeCreate(OrderTypeBase):
    pass


class OrderTypeUpdate(BaseModel):
    branch_id: Optional[int] = None
    name: Optional[str] = Field(default=None, max_length=100)
    code: Optional[str] = Field(default=None, max_length=30)
    order_category: Optional[str] = None
    description: Optional[str] = None
    service_charge_percentage: Optional[Decimal] = None
    minimum_order_amount: Optional[Decimal] = None
    requires_table: Optional[bool] = None
    requires_customer: Optional[bool] = None
    requires_delivery_address: Optional[bool] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class OrderTypeResponse(OrderTypeBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True