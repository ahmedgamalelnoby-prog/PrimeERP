from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models.user import User
from app.modules.saas.entitlements import require_module

router=APIRouter(prefix="/hr",tags=["HR"],dependencies=[Depends(require_module("hr"))])

def _tenant(user:User):
    if user.tenant_id is None: raise HTTPException(403,"User is not assigned to a tenant")
    return user.tenant_id

class WorkforceUpdate(BaseModel):
    full_name:str|None=None; phone:str|None=None; address:str|None=None; preferred_language:str="ar"

@router.get("/workforce")
def workforce(company_id:int=Query(...,gt=0),current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    tenant_id=_tenant(current_user)
    if db.scalar(select(Company).where(Company.id==company_id,Company.tenant_id==tenant_id)) is None: raise HTTPException(403,"Company is outside the current tenant")
    users=list(db.scalars(select(User).where(User.tenant_id==tenant_id,User.is_deleted.is_(False)).order_by(User.full_name,User.id)).all())
    return [{"id":u.id,"username":u.username,"email":u.email,"full_name":u.full_name,"phone":u.phone,"address":u.address,"is_active":u.is_active,"role_id":u.role_id} for u in users]

@router.patch("/workforce/{user_id}")
def update_workforce(user_id:int,payload:WorkforceUpdate,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    tenant_id=_tenant(current_user); obj=db.scalar(select(User).where(User.id==user_id,User.tenant_id==tenant_id,User.is_deleted.is_(False)))
    if obj is None: raise HTTPException(404,"Employee/user not found")
    for key,value in payload.model_dump().items(): setattr(obj,key,value)
    db.commit(); db.refresh(obj)
    return {"id":obj.id,"full_name":obj.full_name,"phone":obj.phone,"address":obj.address,"preferred_language":obj.preferred_language}
