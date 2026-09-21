from fastapi import APIRouter,Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from .enterprise_service import enterprise_completion_service
router=APIRouter(prefix="/enterprise-completion",tags=["Enterprise Completion"])
class ControlPayload(BaseModel):tenant_id:int;company_id:int;module:str;document_type:str;document_id:str;state:str="draft";approval_required:bool=False;approved:bool=False
@router.post("/control")
def control(p:ControlPayload,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
 if not u.is_platform_admin and u.tenant_id!=p.tenant_id: from fastapi import HTTPException;raise HTTPException(403,"Tenant mismatch")
 return enterprise_completion_service.control(db,**p.model_dump())
@router.post("/control/{control_id}/post")
def post(control_id:int,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
 from sqlalchemy import select
 from .enterprise_models import DomainControl
 x=db.scalar(select(DomainControl).where(DomainControl.id==control_id))
 if not x: from fastapi import HTTPException;raise HTTPException(404,"Control not found")
 return enterprise_completion_service.post(db,x)
