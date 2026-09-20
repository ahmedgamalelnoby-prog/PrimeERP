from datetime import datetime
from pydantic import BaseModel, Field
class AppCreate(BaseModel):
    company_id:int=Field(gt=0);name:str=Field(min_length=2,max_length=160);redirect_uris:list[str]=[];scopes:list[str]=[]
class AppResponse(BaseModel):
    id:int;company_id:int;name:str;client_id:str;scopes:list[str];is_active:bool;created_at:datetime
    model_config={"from_attributes":True}
class AppCreated(AppResponse):
    client_secret:str
class KeyCreate(BaseModel):
    app_id:int=Field(gt=0);scopes:list[str]=[];expires_at:datetime|None=None
class KeyCreated(BaseModel):
    id:int;key:str;key_prefix:str;scopes:list[str];expires_at:datetime|None
class WebhookCreate(BaseModel):
    app_id:int=Field(gt=0);url:str=Field(min_length=8,max_length=1000);events:list[str]=[]
class WebhookResponse(BaseModel):
    id:int;app_id:int;url:str;events:list[str];is_active:bool
    model_config={"from_attributes":True}
class WebhookCreated(WebhookResponse):
    signing_secret:str
class EventPublish(BaseModel):
    company_id:int=Field(gt=0);event_id:str=Field(min_length=3,max_length=160);event_type:str=Field(min_length=2,max_length=160);payload:dict
class CustomFieldCreate(BaseModel):
    company_id:int=Field(gt=0);entity_type:str;field_key:str;label:str;field_type:str;required:bool=False;options:list[str]=[]
class CustomFieldResponse(CustomFieldCreate):
    id:int;is_active:bool
    model_config={"from_attributes":True}
