from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from .revaluation_schemas import RevaluationCreate
from .revaluation import inventory_cost_revaluation_service
router=APIRouter(prefix="/inventory/costing/revaluations",tags=["Inventory Cost Revaluation"])
@router.post("")
def create(payload:RevaluationCreate,db:Session=Depends(get_db),current_user=Depends(get_current_user)):
    return inventory_cost_revaluation_service.create(db,tenant_id=current_user.tenant_id,user_id=current_user.id,**payload.model_dump())
@router.post("/{revaluation_id}/post")
def post(revaluation_id:int,db:Session=Depends(get_db),current_user=Depends(get_current_user)):
    return inventory_cost_revaluation_service.post(db,tenant_id=current_user.tenant_id,user_id=current_user.id,revaluation_id=revaluation_id)
