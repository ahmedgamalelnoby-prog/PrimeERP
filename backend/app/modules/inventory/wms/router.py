from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from .schemas import WMSOperationCreate, WMSOperationResponse
from .service import wms_service

router = APIRouter(prefix="/inventory/wms", tags=["inventory-wms"], dependencies=[Depends(require_permission("inventory.access"))])

def _company(db, company_id, user):
    if user.tenant_id is None: raise HTTPException(403, "Tenant required")
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == user.tenant_id, Company.is_active.is_(True)))
    if company is None: raise HTTPException(403, "Company is outside the current tenant")
    return company

@router.get("", response_model=list[WMSOperationResponse])
def list_operations(company_id:int=Query(...,gt=0), operation_type:str|None=None, status:str|None=None, db:Session=Depends(get_db), current_user=Depends(get_current_user)):
    _company(db, company_id, current_user)
    return wms_service.list(db, company_id, operation_type, status)

@router.post("", response_model=WMSOperationResponse, dependencies=[Depends(require_permission("inventory.write"))])
def create_operation(payload:WMSOperationCreate, db:Session=Depends(get_db), current_user=Depends(get_current_user)):
    _company(db, payload.company_id, current_user)
    try:
        op=wms_service.create(db, tenant_id=current_user.tenant_id, user_id=current_user.id, payload=payload)
        db.commit();db.refresh(op);return op
    except ValueError as exc:
        db.rollback();raise HTTPException(422,str(exc)) from exc

@router.post("/{operation_id}/transition", response_model=WMSOperationResponse, dependencies=[Depends(require_permission("inventory.post"))])
def transition(operation_id:int, target:str, company_id:int=Query(...,gt=0), db:Session=Depends(get_db), current_user=Depends(get_current_user)):
    _company(db, company_id, current_user)
    try:
        op=wms_service.transition(db, tenant_id=current_user.tenant_id, user_id=current_user.id, operation_id=operation_id, target=target)
        if op.company_id != company_id: raise HTTPException(403,"WMS operation is outside the selected company")
        db.commit();db.refresh(op);return op
    except ValueError as exc:
        db.rollback();raise HTTPException(409,str(exc)) from exc
