from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from .schemas import WMSOperationCreate, WMSOperationResponse
from .service import wms_service

router = APIRouter(prefix="/inventory/wms", tags=["inventory-wms"])

@router.get("", response_model=list[WMSOperationResponse])
def list_operations(operation_type: str | None = None, status: str | None = None, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return wms_service.list(db, current_user.company_id, operation_type, status)

@router.post("", response_model=WMSOperationResponse)
def create_operation(payload: WMSOperationCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return wms_service.create(db, tenant_id=current_user.tenant_id, user_id=current_user.id, payload=payload)

@router.post("/{operation_id}/transition", response_model=WMSOperationResponse)
def transition(operation_id: int, target: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return wms_service.transition(db, tenant_id=current_user.tenant_id, user_id=current_user.id, operation_id=operation_id, target=target)
