from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
class WarehouseCreate(BaseModel):
    branch_id:int
    code:str=Field(min_length=1,max_length=50)
    name:str=Field(min_length=1,max_length=150)
class WarehouseRead(WarehouseCreate):
    model_config=ConfigDict(from_attributes=True)
    id:int
    tenant_id:int
    is_active:bool
class LocationCreate(BaseModel):
    warehouse_id:int
    parent_id:int|None=None
    code:str=Field(min_length=1,max_length=50)
    name:str=Field(min_length=1,max_length=150)
class LocationRead(LocationCreate):
    model_config=ConfigDict(from_attributes=True)
    id:int
    tenant_id:int
    is_active:bool
class BalanceRead(BaseModel):
    id:int
    warehouse_id:int
    location_id:int
    product_id:int
    quantity:Decimal
    reserved_quantity:Decimal
    available_quantity:Decimal
class MovementCreate(BaseModel):
    product_id:int
    warehouse_id:int
    location_id:int
    quantity:Decimal=Field(gt=0)
    movement_type:str=Field(default="receipt",min_length=2,max_length=30)
    notes:str|None=None
class TransferLineCreate(BaseModel):
    product_id:int
    source_location_id:int
    destination_location_id:int
    quantity:Decimal=Field(gt=0)
class TransferCreate(BaseModel):
    source_warehouse_id:int
    destination_warehouse_id:int
    lines:list[TransferLineCreate]=Field(min_length=1)
    notes:str|None=None
class ReservationLineCreate(BaseModel):
    product_id:int
    location_id:int
    quantity:Decimal=Field(gt=0)
class ReservationCreate(BaseModel):
    reference_type:str=Field(min_length=1,max_length=50)
    reference_id:int
    lines:list[ReservationLineCreate]=Field(min_length=1)
    notes:str|None=None
class IssueLineCreate(BaseModel):
    product_id:int
    location_id:int
    quantity:Decimal=Field(gt=0)
class IssueCreate(BaseModel):
    warehouse_id:int
    issue_type:str="consumption"
    reference_type:str|None=None
    reference_id:int|None=None
    lines:list[IssueLineCreate]=Field(min_length=1)
    notes:str|None=None
