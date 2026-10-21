from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.audit.service import record_audit_event
from app.modules.companies.models import Company
from app.core.context import get_effective_tenant_id
from app.core.permissions import require_permission
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models.user import User
from app.modules.saas.entitlements import require_module

router = APIRouter(
    prefix="/hr",
    tags=["HR"],
    dependencies=[Depends(require_module("hr"))],
)


def _tenant(user: User) -> int:
    if get_effective_tenant_id(user) is None:
        raise HTTPException(403, "User is not assigned to a tenant")
    return get_effective_tenant_id(user)


def _company_for_tenant(db: Session, company_id: int, tenant_id: int) -> Company:
    company = db.scalar(
        select(Company).where(
            Company.id == company_id,
            Company.tenant_id == tenant_id,
        )
    )
    if company is None:
        # Do not disclose whether a company exists in another tenant.
        raise HTTPException(404, "Company not found")
    return company


class WorkforceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str | None = Field(default=None, min_length=1, max_length=150)
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=1000)
    preferred_language: Literal["ar", "en"] = "ar"


@router.get(
    "/workforce",
    dependencies=[Depends(require_permission("enterprise.access"))],
)
def workforce(
    company_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tenant_id = _tenant(current_user)
    _company_for_tenant(db, company_id, tenant_id)

    users = list(
        db.scalars(
            select(User)
            .where(
                User.tenant_id == tenant_id,
                User.is_deleted.is_(False),
            )
            .order_by(User.full_name, User.id)
        ).all()
    )
    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "phone": user.phone,
            "address": user.address,
            "is_active": user.is_active,
            "role_id": user.role_id,
        }
        for user in users
    ]


@router.patch(
    "/workforce/{user_id}",
    dependencies=[Depends(require_permission("enterprise.write"))],
)
def update_workforce(
    user_id: int,
    payload: WorkforceUpdate,
    company_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tenant_id = _tenant(current_user)
    _company_for_tenant(db, company_id, tenant_id)

    obj = db.scalar(
        select(User).where(
            User.id == user_id,
            User.tenant_id == tenant_id,
            User.is_deleted.is_(False),
        )
    )
    if obj is None:
        raise HTTPException(404, "Employee/user not found")

    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(422, "At least one workforce field must be supplied")

    for key, value in changes.items():
        setattr(obj, key, value)

    record_audit_event(
        db,
        action="hr.workforce_profile_updated",
        entity_type="user",
        entity_id=obj.id,
        user_id=current_user.id,
        tenant_id=tenant_id,
        company_id=company_id,
        metadata={"changed_fields": sorted(changes)},
    )
    db.commit()
    db.refresh(obj)
    return {
        "id": obj.id,
        "full_name": obj.full_name,
        "phone": obj.phone,
        "address": obj.address,
        "preferred_language": obj.preferred_language,
    }
