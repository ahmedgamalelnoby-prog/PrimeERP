from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from .schemas import CustomerCreate, CustomerRead, CustomerUpdate
from .service import customer_service
router=APIRouter(prefix="/customers",tags=["customers"])
def _tenant(user:User)->int:
    if user.is_platform_admin or user.tenant_id is None: raise HTTPException(status_code=403,detail="Active tenant context is required")
    return user.tenant_id
@router.get("",response_model=list[CustomerRead])
def list_customers(active_only:bool=Query(False),search:str|None=Query(None),db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    return customer_service.list(db,_tenant(current_user),active_only,search)
@router.get("/{customer_id}",response_model=CustomerRead)
def get_customer(customer_id:int,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    return customer_service.get(db,_tenant(current_user),customer_id)
@router.post("",response_model=CustomerRead,status_code=status.HTTP_201_CREATED)
def create_customer(payload:CustomerCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    return customer_service.create(db,_tenant(current_user),payload)
@router.put("/{customer_id}",response_model=CustomerRead)
def update_customer(customer_id:int,payload:CustomerUpdate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    return customer_service.update(db,_tenant(current_user),customer_id,payload)
