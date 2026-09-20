from datetime import date
from decimal import Decimal
from pydantic import BaseModel,Field
class EntityCreate(BaseModel): company_id:int=Field(gt=0); code:str; name:str; functional_currency:str="EGP"; consolidation_method:str="full"
class EntityResponse(EntityCreate): id:int; is_active:bool; model_config={"from_attributes":True}
class GroupCreate(BaseModel): company_id:int=Field(gt=0); code:str; name:str; reporting_currency:str="EGP"
class GroupResponse(GroupCreate): id:int; is_active:bool; model_config={"from_attributes":True}
class MemberCreate(BaseModel): entity_id:int; ownership_percent:Decimal=Field(ge=0,le=100); consolidation_percent:Decimal=Field(ge=0,le=100); active_from:date|None=None; active_to:date|None=None
class IntercompanyCreate(BaseModel): company_id:int; from_entity_id:int; to_entity_id:int; reference:str; transaction_date:date; account_code:str; amount:Decimal=Field(gt=0); currency_code:str="EGP"; description:str|None=None
class FxRateCreate(BaseModel): company_id:int; rate_date:date; from_currency:str; to_currency:str; rate:Decimal=Field(gt=0)
class RevaluationCreate(BaseModel): company_id:int; revaluation_date:date; account_code:str; currency_code:str; base_amount:Decimal; old_rate:Decimal=Field(gt=0); new_rate:Decimal=Field(gt=0); reason:str|None=None
class ConsolidationRunCreate(BaseModel): group_id:int; period_start:date; period_end:date
