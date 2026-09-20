from datetime import datetime,timezone
from decimal import Decimal
from fastapi import APIRouter,Depends,Query,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.companies.models import Company
from .completion_models import POSModifierGroup,POSModifierOption,POSPromotion

router=APIRouter(prefix="/pos/completion",tags=["POS Completion"])
def company(db,cid,u):
    if u.tenant_id is None: raise HTTPException(403,"Tenant required")
    x=db.scalar(select(Company).where(Company.id==cid,Company.tenant_id==u.tenant_id,Company.is_active.is_(True)))
    if x is None: raise HTTPException(403,"Company is outside the current tenant")
class GroupPayload(BaseModel):
    name:str=Field(min_length=1,max_length=120);min_select:int=Field(default=0,ge=0);max_select:int=Field(default=1,ge=0)
class OptionPayload(BaseModel):
    group_id:int=Field(gt=0);code:str=Field(min_length=1,max_length=60);name:str=Field(min_length=1,max_length=160);price_delta:float=0
class PromotionPayload(BaseModel):
    code:str=Field(min_length=1,max_length=80);name:str=Field(min_length=1,max_length=160);discount_percent:float=Field(ge=0,le=100);min_subtotal:float=Field(default=0,ge=0);max_discount:float|None=Field(default=None,ge=0);valid_from:datetime|None=None;valid_to:datetime|None=None
@router.post("/modifier-groups",status_code=201)
def create_group(p:GroupPayload,company_id:int=Query(...,gt=0),db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    company(db,company_id,u);x=POSModifierGroup(company_id=company_id,**p.model_dump());db.add(x);db.commit();db.refresh(x);return x
@router.post("/modifier-options",status_code=201)
def create_option(p:OptionPayload,company_id:int=Query(...,gt=0),db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    company(db,company_id,u);g=db.scalar(select(POSModifierGroup).where(POSModifierGroup.id==p.group_id,POSModifierGroup.company_id==company_id,POSModifierGroup.is_active.is_(True)))
    if g is None: raise HTTPException(422,"Modifier group is outside the company")
    x=POSModifierOption(**p.model_dump());db.add(x);db.commit();db.refresh(x);return x
@router.get("/modifier-groups")
def list_groups(company_id:int=Query(...,gt=0),db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    company(db,company_id,u);return list(db.scalars(select(POSModifierGroup).where(POSModifierGroup.company_id==company_id,POSModifierGroup.is_active.is_(True)).order_by(POSModifierGroup.id)).all())
@router.post("/promotions",status_code=201)
def create_promotion(p:PromotionPayload,company_id:int=Query(...,gt=0),db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    company(db,company_id,u)
    if p.valid_from and p.valid_to and p.valid_to < p.valid_from:
        raise HTTPException(422,"Promotion valid_to cannot be earlier than valid_from")
    if db.scalar(select(POSPromotion).where(POSPromotion.company_id==company_id,POSPromotion.code==p.code)): raise HTTPException(409,"Promotion code already exists")
    x=POSPromotion(company_id=company_id,**p.model_dump());db.add(x);db.commit();db.refresh(x);return x
@router.get("/promotions/validate")
def validate_promotion(code:str,subtotal:float,company_id:int=Query(...,gt=0),db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    company(db,company_id,u);now=datetime.now(timezone.utc)
    x=db.scalar(select(POSPromotion).where(POSPromotion.company_id==company_id,POSPromotion.code==code,POSPromotion.is_active.is_(True)))
    if x is None: raise HTTPException(404,"Promotion not found")
    if x.valid_from and now<x.valid_from or x.valid_to and now>x.valid_to: raise HTTPException(409,"Promotion is outside its validity window")
    base=Decimal(str(subtotal))
    if base<Decimal(x.min_subtotal or 0): return {"eligible":False,"discount":0,"reason":"minimum subtotal not met"}
    discount=(base*Decimal(x.discount_percent or 0)/Decimal("100"))
    if x.max_discount is not None: discount=min(discount,Decimal(x.max_discount))
    return {"eligible":True,"promotion_id":x.id,"code":x.code,"discount":discount,"discount_percent":x.discount_percent}
