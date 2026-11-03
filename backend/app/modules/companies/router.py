from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.context import get_effective_tenant_id
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.identity.models.user_company_access import UserCompanyAccess
from app.modules.companies.access import accessible_company_query, require_company_access
from app.modules.companies.schemas import CompanyCreate, CompanyResponse, CompanyUpdate
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.saas.entitlements import enforce_company_limit

router = APIRouter(prefix="/companies", tags=["Companies"])


def _tenant_id(user: User) -> int:
    return get_effective_tenant_id(user)


def _get_company(db: Session, company_id: int, user: User) -> Company:
    return require_company_access(db, user, company_id)


@router.get("", response_model=list[CompanyResponse], dependencies=[Depends(require_permission("company.access"))])
def list_companies(active_only: bool = Query(False), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = accessible_company_query(current_user, active_only=active_only).order_by(Company.name, Company.id)
    companies = list(db.scalars(stmt).all())
    if current_user.is_platform_admin:
        return [{**CompanyResponse.model_validate(company).model_dump(), "is_default": False} for company in companies]
    defaults = set(db.scalars(select(UserCompanyAccess.company_id).where(
        UserCompanyAccess.user_id == current_user.id,
        UserCompanyAccess.is_default.is_(True),
    )).all())
    return [
        {**CompanyResponse.model_validate(company).model_dump(), "is_default": company.id in defaults}
        for company in companies
    ]


@router.get("/{company_id}", response_model=CompanyResponse, dependencies=[Depends(require_permission("company.access"))])
def get_company(company_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _get_company(db, company_id, current_user)


@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("company.write"))])
def create_company(payload: CompanyCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tenant_id = _tenant_id(current_user)
    enforce_company_limit(db, tenant_id)
    company = Company(tenant_id=tenant_id, **payload.model_dump())
    db.add(company)
    try:
        db.flush()
        if not current_user.is_platform_admin:
            has_default = db.scalar(select(UserCompanyAccess.user_id).where(
                UserCompanyAccess.user_id == current_user.id,
                UserCompanyAccess.is_default.is_(True),
            ).limit(1))
            db.add(UserCompanyAccess(
                user_id=current_user.id,
                company_id=company.id,
                is_default=has_default is None,
            ))
        db.commit()
        db.refresh(company)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Company code already exists for this tenant") from exc
    return company


@router.patch("/{company_id}", response_model=CompanyResponse, dependencies=[Depends(require_permission("company.write"))])
def update_company(company_id: int, payload: CompanyUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    company = _get_company(db, company_id, current_user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(company, field, value.strip() if isinstance(value, str) else value)
    try:
        db.commit()
        db.refresh(company)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Company code already exists for this tenant") from exc
    return company


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permission("company.write"))])
def deactivate_company(company_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    company = _get_company(db, company_id, current_user)
    company.is_active = False
    db.commit()


@router.put("/{company_id}/users/{user_id}/access", status_code=status.HTTP_200_OK,
            dependencies=[Depends(require_permission("company.write"))])
def grant_company_access(
    company_id: int,
    user_id: int,
    is_default: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = _get_company(db, company_id, current_user)
    target_user = db.scalar(select(User).where(
        User.id == user_id,
        User.tenant_id == company.tenant_id,
        User.is_deleted.is_(False),
    ))
    if target_user is None:
        raise HTTPException(status_code=404, detail="User not found in this tenant")
    access = db.get(UserCompanyAccess, (user_id, company_id))
    if access is None:
        access = UserCompanyAccess(user_id=user_id, company_id=company_id, is_default=False)
        db.add(access)
    if is_default:
        db.query(UserCompanyAccess).filter(
            UserCompanyAccess.user_id == user_id
        ).update({UserCompanyAccess.is_default: False}, synchronize_session=False)
        access.is_default = True
    elif db.scalar(select(UserCompanyAccess.user_id).where(
        UserCompanyAccess.user_id == user_id,
        UserCompanyAccess.is_default.is_(True),
    ).limit(1)) is None:
        access.is_default = True
    db.commit()
    return {"user_id": user_id, "company_id": company_id, "is_default": access.is_default}


@router.delete("/{company_id}/users/{user_id}/access", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_permission("company.write"))])
def revoke_company_access(
    company_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = _get_company(db, company_id, current_user)
    target_user = db.scalar(select(User).where(
        User.id == user_id,
        User.tenant_id == company.tenant_id,
        User.is_deleted.is_(False),
    ))
    if target_user is None:
        raise HTTPException(status_code=404, detail="User not found in this tenant")
    access = db.get(UserCompanyAccess, (user_id, company_id))
    if access is None:
        return
    was_default = access.is_default
    db.delete(access)
    db.flush()
    if was_default:
        replacement = db.scalar(select(UserCompanyAccess).where(
            UserCompanyAccess.user_id == user_id
        ).order_by(UserCompanyAccess.company_id).limit(1))
        if replacement is not None:
            replacement.is_default = True
    db.commit()
