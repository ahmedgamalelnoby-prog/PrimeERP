from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.companies.models import Company
from app.modules.branches.models import Branch

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/summary")
def get_dashboard_summary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tenant_id = current_user.tenant_id
    if tenant_id is None:
        return {"tenant": None, "users": {"total": 0, "active": 0}, "companies": {"total": 0, "active": 0}, "branches": {"total": 0, "active": 0}}
    users_total = db.scalar(select(func.count(User.id)).where(User.tenant_id == tenant_id, User.is_deleted.is_(False))) or 0
    users_active = db.scalar(select(func.count(User.id)).where(User.tenant_id == tenant_id, User.is_deleted.is_(False), User.is_active.is_(True))) or 0
    companies_total = db.scalar(select(func.count(Company.id)).where(Company.tenant_id == tenant_id)) or 0
    companies_active = db.scalar(select(func.count(Company.id)).where(Company.tenant_id == tenant_id, Company.is_active.is_(True))) or 0
    branches_total = db.scalar(select(func.count(Branch.id)).where(Branch.tenant_id == tenant_id)) or 0
    branches_active = db.scalar(select(func.count(Branch.id)).where(Branch.tenant_id == tenant_id, Branch.is_active.is_(True))) or 0
    tenant = current_user.tenant
    return {
        "tenant": {"id": tenant.id if tenant else tenant_id, "name": tenant.name if tenant else None, "slug": tenant.slug if tenant else None},
        "users": {"total": users_total, "active": users_active},
        "companies": {"total": companies_total, "active": companies_active},
        "branches": {"total": branches_total, "active": branches_active},
    }