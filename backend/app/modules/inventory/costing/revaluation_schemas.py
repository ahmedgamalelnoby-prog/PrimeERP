from datetime import date
from decimal import Decimal
from pydantic import BaseModel,Field
class RevaluationCreate(BaseModel):
    company_id:int=Field(gt=0); item_id:int=Field(gt=0); warehouse_id:int=Field(gt=0); new_unit_cost:Decimal=Field(ge=0); effective_date:date; reason:str=Field(min_length=3,max_length=500)
