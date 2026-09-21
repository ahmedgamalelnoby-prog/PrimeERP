from fastapi import APIRouter,Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from .finance_service import finance_completion_service
router=APIRouter(prefix="/completion/finance",tags=["Finance Completion"])
class Allocation(BaseModel):tenant_id:int;company_id:int;direction:str;partner_id:int;source_type:str;source_id:str;target_type:str;target_id:str;amount:float;currency_code:str="EGP"
@router.post("/allocations")
def allocation(p:Allocation,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
 if not u.is_platform_admin and u.tenant_id!=p.tenant_id:from fastapi import HTTPException;raise HTTPException(403,"Tenant mismatch")
 return finance_completion_service.allocate(db,**p.model_dump())
