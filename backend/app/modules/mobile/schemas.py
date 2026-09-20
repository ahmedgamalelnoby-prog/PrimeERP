from datetime import datetime
from pydantic import BaseModel, Field
class DeviceRegister(BaseModel):
    company_id:int=Field(gt=0); device_uid:str=Field(min_length=3,max_length=160); name:str=Field(min_length=1,max_length=160); platform:str=Field(min_length=2,max_length=30); app_version:str|None=None
class DeviceResponse(DeviceRegister):
    id:int; is_active:bool; last_seen_at:datetime|None=None
    model_config={"from_attributes":True}
class SessionCreate(BaseModel): device_id:int=Field(gt=0); warehouse_id:int|None=None; branch_id:int|None=None
class SessionResponse(BaseModel):
    id:int; device_id:int; user_id:int; warehouse_id:int|None; branch_id:int|None; status:str; opened_at:datetime; closed_at:datetime|None
    model_config={"from_attributes":True}
class SyncItem(BaseModel): operation_id:str=Field(min_length=3,max_length=160); operation_type:str=Field(min_length=2,max_length=80); payload:dict
class SyncBatch(BaseModel): device_id:int=Field(gt=0); operations:list[SyncItem]=Field(max_length=200)
class TaskCreate(BaseModel):
    company_id:int=Field(gt=0); assigned_user_id:int|None=None; task_type:str; title:str; reference_type:str|None=None; reference_id:int|None=None; payload:dict={}
class TaskResponse(BaseModel):
    id:int; company_id:int; assigned_user_id:int|None; task_type:str; reference_type:str|None; reference_id:int|None; title:str; payload:dict; status:str; due_at:datetime|None; completed_at:datetime|None
    model_config={"from_attributes":True}
class ScanCreate(BaseModel): session_id:int=Field(gt=0); barcode:str=Field(min_length=1,max_length=160); symbology:str|None=None; context:str=Field(min_length=2,max_length=60); payload:dict|None=None
class ScanResponse(BaseModel):
    id:int; barcode:str; symbology:str|None; context:str; scanned_at:datetime
    model_config={"from_attributes":True}
