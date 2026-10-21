from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from .schemas import CompanyCreate, CompanyRead, CompanyUpdate
from .service import company_service

router = APIRouter(prefix="/companies", tags=["companies"])

def tenant_id(user: User) -> int:
    if user.is_platform_admin or user.tenant_id is None: raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Active tenant context is required")
    return user.tenant_id

@router.get("", response_model=list[CompanyRead])
def list_companies(active_only: bool = Query(False), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return company_service.list(db, tenant_id(current_user), active_only)

@router.get("/{company_id}", response_model=CompanyRead)
def get_company(company_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return company_service.get(db, tenant_id(current_user), company_id)

@router.post("", response_model=CompanyRead, status_code=status.HTTP_201_CREATED)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return company_service.create(db, tenant_id(current_user), payload)

@router.put("/{company_id}", response_model=CompanyRead)
def update_company(company_id: int, payload: CompanyUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return company_service.update(db, tenant_id(current_user), company_id, payload)
