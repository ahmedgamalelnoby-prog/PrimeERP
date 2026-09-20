from decimal import Decimal
from typing import Literal
from pydantic import BaseModel,Field
class WasteCreate(BaseModel):
 company_id:int=Field(gt=0);item_id:int=Field(gt=0);variant_id:int|None=Field(default=None,gt=0);location_id:int=Field(gt=0);quantity:Decimal=Field(gt=0);unit_cost:Decimal=Field(default=0,ge=0);waste_type:Literal["scrap","damaged","expired","spoilage","production_waste"];reason:str=Field(min_length=1);reference:str|None=None
class WasteResponse(WasteCreate):
 id:int;status:str;posted_at:object|None=None
 model_config={"from_attributes":True}