from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.context import get_effective_tenant_id
from app.modules.companies.models import Company
from app.modules.identity.models.user_company_access import UserCompanyAccess
from app.modules.identity.models import User


def accessible_company_query(user: User, *, active_only: bool = True):
    tenant_id = get_effective_tenant_id(user)
    stmt = select(Company).where(Company.tenant_id == tenant_id)
    if active_only:
        stmt = stmt.where(Company.is_active.is_(True))
    if not user.is_platform_admin:
        stmt = stmt.join(
            UserCompanyAccess,
            UserCompanyAccess.company_id == Company.id,
        ).where(UserCompanyAccess.user_id == user.id)
    return stmt


def require_company_access(
    db: Session,
    user: User,
    company_id: int,
    *,
    active_only: bool = True,
) -> Company:
    company = db.scalar(
        accessible_company_query(user, active_only=active_only).where(
            Company.id == company_id
        )
    )
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return company
