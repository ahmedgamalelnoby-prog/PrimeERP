from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from .schemas import BranchCreate, BranchRead, BranchUpdate
from .service import branch_service
router=APIRouter(prefix="/branches", tags=["branches"])
def tenant_id(user: User)->int:
    if user.is_platform_admin or user.tenant_id is None: raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Active tenant context is required")
    return user.tenant_id
@router.get("",response_model=list[BranchRead])
def list_branches(company_id:int|None=Query(default=None,gt=0),db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    tid=tenant_id(current_user)
    if company_id is not None: branch_service._company(db,tid,company_id)
    return branch_service.list(db,tid,company_id)
@router.get("/{branch_id}",response_model=BranchRead)
def get_branch(branch_id:int,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    return branch_service.get(db,tenant_id(current_user),branch_id)
@router.post("",response_model=BranchRead,status_code=status.HTTP_201_CREATED)
def create_branch(payload:BranchCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    return branch_service.create(db,tenant_id(current_user),payload)
@router.put("/{branch_id}",response_model=BranchRead)
def update_branch(branch_id:int,payload:BranchUpdate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    return branch_service.update(db,tenant_id(current_user),branch_id,payload)
