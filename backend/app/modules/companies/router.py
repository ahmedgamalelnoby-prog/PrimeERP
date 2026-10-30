from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.context import get_effective_tenant_id, get_optional_request_context
from app.core.permissions import require_permission
from app.core.permissions.checker import can_assign_role, effective_role_id
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.branches.models import Branch
from app.modules.branches.membership import BranchUserMembership
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
    context = get_optional_request_context()
    if context is None or context.company_id != company_id:
        raise HTTPException(status_code=403, detail="Select the requested company using X-Company-ID")
    if context.branch_id is not None:
        raise HTTPException(status_code=400, detail="Company administration is company-wide; omit X-Branch-ID")
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


@router.get("/{company_id}/assignable-roles", dependencies=[Depends(require_permission("company.write"))])
def list_assignable_company_roles(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List only active roles this actor is allowed to grant in this company."""
    _get_company(db, company_id, current_user)
    roles = db.scalars(select(Role).where(Role.is_active.is_(True)).order_by(Role.name)).all()
    return [
        {"id": role.id, "name": role.name, "description": role.description}
        for role in roles
        if can_assign_role(current_user, role.id, db)
    ]


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
    member_user = db.scalar(
        select(User).where(
            User.id == user_id,
            User.tenant_id == company.tenant_id,
            User.is_deleted.is_(False),
        )
    )
    if member_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found in this tenant")
    if not member_user.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot grant company access to a disabled user")

    membership = db.scalar(
        select(CompanyUserMembership)
        .where(
            CompanyUserMembership.company_id == company.id,
            CompanyUserMembership.user_id == member_user.id,
        )
        .with_for_update()
    )
    assigned_role_id = role_id
    if membership is None and assigned_role_id is None:
        if current_user.is_platform_admin:
            assigned_role_id = member_user.role_id
        else:
            # New grants inherit the actor's effective company role, never the
            # target user's global role (which could be more privileged).
            assigned_role_id = effective_role_id(current_user, db)
    if assigned_role_id is not None and not can_assign_role(current_user, assigned_role_id, db):
        raise HTTPException(status_code=403, detail="You cannot assign a role beyond your own permissions")

    if membership is None:
        membership = CompanyUserMembership(
            company_id=company.id,
            user_id=member_user.id,
            is_active=True,
            assigned_by=current_user.id,
            role_id=assigned_role_id,
        )
        db.add(membership)
    else:
        membership.is_active = True
        membership.assigned_by = current_user.id
    if assigned_role_id is not None:
        membership.role_id = assigned_role_id
    db.flush()
    record_audit_event(
        db,
        action="company.membership.grant",
        entity_type="company_user_membership",
        entity_id=membership.id,
        user_id=current_user.id,
        tenant_id=company.tenant_id,
        metadata={"company_id": company.id, "member_user_id": member_user.id, "role_id": membership.role_id},
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
    previous_role_id = membership.role_id
    membership.is_active = False
    record_audit_event(
        db,
        action="company.membership.revoke",
        entity_type="company_user_membership",
        entity_id=membership.id,
        user_id=current_user.id,
        tenant_id=company.tenant_id,
        metadata={"company_id": company.id, "member_user_id": user_id, "previous_role_id": previous_role_id},
    )
    db.commit()
    return None


@router.delete("/{company_id}/members/{user_id}/role", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permission("company.write"))])
def clear_company_member_role(
    company_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = _get_company(db, company_id, current_user)
    membership = db.scalar(
        select(CompanyUserMembership).where(
            CompanyUserMembership.company_id == company.id,
            CompanyUserMembership.user_id == user_id,
        ).with_for_update()
    )
    if membership is None:
        raise HTTPException(status_code=404, detail="Company membership not found")
    previous_role_id = membership.role_id
    membership.role_id = None
    record_audit_event(
        db,
        action="company.membership.role.clear",
        entity_type="company_user_membership",
        entity_id=membership.id,
        user_id=current_user.id,
        tenant_id=company.tenant_id,
        metadata={"company_id": company.id, "member_user_id": user_id, "previous_role_id": previous_role_id},
    )
    db.commit()
    return None


@router.get(
    "/{company_id}/membership-audit",
    dependencies=[
        Depends(require_permission("company.write")),
        Depends(require_permission("branch.write")),
    ],
)
def list_company_membership_audit(
    company_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return a tenant-scoped, paginated company/branch access review."""
    company = _get_company(db, company_id, current_user)

    total = db.scalar(
        select(func.count(User.id)).where(
            User.tenant_id == company.tenant_id,
            User.is_deleted.is_(False),
        )
    ) or 0

    member_rows = db.execute(
        select(User, CompanyUserMembership, Role)
        .outerjoin(
            CompanyUserMembership,
            and_(
                CompanyUserMembership.company_id == company.id,
                CompanyUserMembership.user_id == User.id,
            ),
        )
        .outerjoin(Role, Role.id == CompanyUserMembership.role_id)
        .where(
            User.tenant_id == company.tenant_id,
            User.is_deleted.is_(False),
        )
        .order_by(User.username, User.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    branches = db.execute(
        select(Branch.id, Branch.name, Branch.code, Branch.is_active)
        .where(
            Branch.company_id == company.id,
            Branch.tenant_id == company.tenant_id,
        )
        .order_by(Branch.name, Branch.id)
    ).all()

    user_ids = [user.id for user, _, _ in member_rows]
    branch_memberships = []
    if user_ids:
        branch_memberships = db.execute(
            select(BranchUserMembership, Branch, Role)
            .join(Branch, Branch.id == BranchUserMembership.branch_id)
            .outerjoin(Role, Role.id == BranchUserMembership.role_id)
            .where(
                Branch.company_id == company.id,
                Branch.tenant_id == company.tenant_id,
                BranchUserMembership.user_id.in_(user_ids),
            )
        ).all()

    branch_access_by_user: dict[int, dict[int, dict]] = {
        user_id: {} for user_id in user_ids
    }
    for membership, branch, role in branch_memberships:
        branch_access_by_user[membership.user_id][branch.id] = {
            "membership_is_active": membership.is_active,
            "role_id": membership.role_id,
            "role_name": role.name if role else None,
        }

    items = []
    for user, membership, role in member_rows:
        items.append({
            "user_id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "user_is_active": user.is_active and not user.is_deleted,
            "company_membership_is_active": membership.is_active if membership else None,
            "company_role_id": membership.role_id if membership else None,
            "company_role_name": role.name if role else None,
            "branch_access": [
                {
                    "branch_id": branch_id,
                    "membership_is_active": branch_access_by_user[user.id].get(branch_id, {}).get("membership_is_active"),
                    "role_id": branch_access_by_user[user.id].get(branch_id, {}).get("role_id"),
                    "role_name": branch_access_by_user[user.id].get(branch_id, {}).get("role_name"),
                }
                for branch_id, _, _, _ in branches
            ],
        })

    return {
        "company_id": company.id,
        "company_name": company.name,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": (total + page_size - 1) // page_size,
        "branches": [
            {"id": branch_id, "name": name, "code": code, "is_active": is_active}
            for branch_id, name, code, is_active in branches
        ],
        "items": items,
    }


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


@router.get("/accessible")
def list_accessible_companies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return only active companies the authenticated user may select."""
    stmt = select(Company).where(
        Company.tenant_id == _tenant_id(current_user),
        Company.is_active.is_(True),
    )
    if not current_user.is_platform_admin:
        stmt = stmt.join(
            CompanyUserMembership,
            CompanyUserMembership.company_id == Company.id,
        ).where(
            CompanyUserMembership.user_id == current_user.id,
            CompanyUserMembership.is_active.is_(True),
        )
    return [
        {"id": company.id, "name": company.name, "code": company.code}
        for company in db.scalars(stmt.order_by(Company.name, Company.id)).unique().all()
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
            db.add(CompanyUserMembership(
                company_id=company.id,
                user_id=current_user.id,
                is_active=True,
                assigned_by=current_user.id,
                role_id=current_user.role_id,
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
