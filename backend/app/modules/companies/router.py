from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.context import get_effective_tenant_id, get_optional_request_context
from app.core.permissions import require_permission
from app.core.permissions.checker import can_assign_role
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.companies.membership import CompanyUserMembership
from app.modules.companies.schemas import CompanyCreate, CompanyResponse, CompanyUpdate
from app.modules.audit.service import record_audit_event
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.roles.models import Role
from app.modules.saas.entitlements import enforce_company_limit

router = APIRouter(prefix="/companies", tags=["Companies"])


def _tenant_id(user: User) -> int:
    return get_effective_tenant_id(user)


def _get_company(db: Session, company_id: int, user: User) -> Company:
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == _tenant_id(user)))
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    if not user.is_platform_admin:
        membership = db.scalar(
            select(CompanyUserMembership.id).where(
                CompanyUserMembership.company_id == company.id,
                CompanyUserMembership.user_id == user.id,
                CompanyUserMembership.is_active.is_(True),
            )
        )
        if membership is None:
            raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.get("/current", response_model=CompanyResponse, dependencies=[Depends(require_permission("company.access"))])
def get_current_company(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the active company selected for this request via X-Company-ID."""
    context = get_optional_request_context()
    company_id = context.company_id if context is not None else None
    if company_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No company is selected. Send a valid X-Company-ID header.",
        )
    company = db.scalar(
        select(Company).where(
            Company.id == company_id,
            Company.tenant_id == _tenant_id(current_user),
            Company.is_active.is_(True),
        )
    )
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Selected company is no longer available")
    return company


@router.get("/{company_id}/members", dependencies=[Depends(require_permission("company.write"))])
def list_company_members(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = _get_company(db, company_id, current_user)
    rows = db.execute(
        select(CompanyUserMembership, User)
        .join(User, User.id == CompanyUserMembership.user_id)
        .where(CompanyUserMembership.company_id == company.id)
        .order_by(User.username, User.id)
    ).all()
    return [
        {
            "user_id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "user_is_active": user.is_active and not user.is_deleted,
            "membership_is_active": membership.is_active,
            "role_id": membership.role_id,
            "created_at": membership.created_at,
        }
        for membership, user in rows
    ]


@router.put("/{company_id}/members/{user_id}", dependencies=[Depends(require_permission("company.write"))])
def grant_company_membership(
    company_id: int,
    user_id: int,
    role_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = _get_company(db, company_id, current_user)
    if role_id is not None:
        if not can_assign_role(current_user, role_id, db):
            raise HTTPException(status_code=403, detail="You cannot assign a role beyond your own permissions")
    member_user = db.scalar(
        select(User).where(
            User.id == user_id,
            User.tenant_id == company.tenant_id,
            User.is_deleted.is_(False),
        )
    )
    if member_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found in this tenant")

    membership = db.scalar(
        select(CompanyUserMembership)
        .where(
            CompanyUserMembership.company_id == company.id,
            CompanyUserMembership.user_id == member_user.id,
        )
        .with_for_update()
    )
    if membership is None:
        membership = CompanyUserMembership(
            company_id=company.id,
            user_id=member_user.id,
            is_active=True,
            assigned_by=current_user.id,
        )
        db.add(membership)
    else:
        membership.is_active = True
        membership.assigned_by = current_user.id
    if role_id is not None:
        membership.role_id = role_id
    db.flush()
    record_audit_event(
        db,
        action="company.membership.grant",
        entity_type="company_user_membership",
        entity_id=membership.id,
        user_id=current_user.id,
        tenant_id=company.tenant_id,
        metadata={"company_id": company.id, "member_user_id": member_user.id},
    )
    db.commit()
    db.refresh(membership)
    return {
        "company_id": company.id,
        "user_id": member_user.id,
        "is_active": membership.is_active,
        "role_id": membership.role_id,
    }


@router.delete("/{company_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permission("company.write"))])
def revoke_company_membership(
    company_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = _get_company(db, company_id, current_user)
    membership = db.scalar(
        select(CompanyUserMembership)
        .where(
            CompanyUserMembership.company_id == company.id,
            CompanyUserMembership.user_id == user_id,
        )
        .with_for_update()
    )
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company membership not found")
    membership.is_active = False
    record_audit_event(
        db,
        action="company.membership.revoke",
        entity_type="company_user_membership",
        entity_id=membership.id,
        user_id=current_user.id,
        tenant_id=company.tenant_id,
        metadata={"company_id": company.id, "member_user_id": user_id},
    )
    db.commit()
    return None


@router.get("", response_model=list[CompanyResponse], dependencies=[Depends(require_permission("company.access"))])
def list_companies(active_only: bool = Query(False), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(Company).where(Company.tenant_id == _tenant_id(current_user)).order_by(Company.name, Company.id)
    if not current_user.is_platform_admin:
        stmt = stmt.join(
            CompanyUserMembership,
            CompanyUserMembership.company_id == Company.id,
        ).where(
            CompanyUserMembership.user_id == current_user.id,
            CompanyUserMembership.is_active.is_(True),
        )
    if active_only:
        stmt = stmt.where(Company.is_active.is_(True))
    return list(db.scalars(stmt).unique().all())


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
            db.add(CompanyUserMembership(
                company_id=company.id,
                user_id=current_user.id,
                is_active=True,
                assigned_by=current_user.id,
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
