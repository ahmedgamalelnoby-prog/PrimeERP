from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from pydantic import BaseModel,Field
from app.database.session import get_db
from app.core.permissions import require_permission
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.core_integration.models import IntegrationTransaction
from app.modules.core_integration.service import core_integration_service
router=APIRouter(prefix="/core/integration",tags=["Core Integration"],dependencies=[Depends(require_permission("system.access"))])
class ReverseRequest(BaseModel): reason:str=Field(min_length=3,max_length=500)
@router.get("/transactions")
def transactions(company_id:int,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 return [x for x in db.scalars(select(IntegrationTransaction).where(IntegrationTransaction.company_id==company_id,IntegrationTransaction.tenant_id==current_user.tenant_id).order_by(IntegrationTransaction.id.desc()).limit(200)).all()]
@router.post("/transactions/{transaction_id}/reverse")
def reverse(transaction_id:int,p:ReverseRequest,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 x=db.scalar(select(IntegrationTransaction).where(IntegrationTransaction.id==transaction_id,IntegrationTransaction.tenant_id==current_user.tenant_id).with_for_update())
 if x is None:raise HTTPException(404,"Integration transaction not found")
 r=core_integration_service.reverse(db,x,current_user,p.reason);db.commit();return {"transaction_id":r.id,"reversal_of_id":x.id,"status":r.status}
