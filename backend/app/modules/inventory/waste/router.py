from fastapi import APIRouter,Depends,HTTPException,Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.permissions import require_permission
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.companies.models import Company
from app.modules.inventory.waste.schemas import WasteCreate,WasteResponse
from app.modules.inventory.waste.service import inventory_waste_service
router=APIRouter(prefix="/inventory/waste",tags=["Inventory Waste"],dependencies=[Depends(require_permission("inventory.access"))])
def guard(db,c,u):
 if not u.tenant_id or not db.scalar(select(Company).where(Company.id==c,Company.tenant_id==u.tenant_id)):raise HTTPException(403,"Company is outside tenant")
@router.post("",response_model=WasteResponse)
def create(p:WasteCreate,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
 guard(db,p.company_id,u);return inventory_waste_service.create(db,p,u.id)
@router.post("/{waste_id}/approve",response_model=WasteResponse)
def approve(waste_id:int,company_id:int=Query(...),db:Session=Depends(get_db),u:User=Depends(get_current_user)):
 guard(db,company_id,u);return inventory_waste_service.approve(db,company_id,waste_id)
@router.post("/{waste_id}/post",response_model=WasteResponse)
def post(waste_id:int,company_id:int=Query(...),db:Session=Depends(get_db),u:User=Depends(get_current_user)):
 guard(db,company_id,u);x=inventory_waste_service.post(db,u.tenant_id,company_id,waste_id,u.id);db.commit();return x