from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.core.context import get_effective_tenant_id
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.roles.models import Role
from app.modules.saas.models import Tenant
from app.modules.saas.schemas import (
    TenantRegistrationRequest,
    TenantRegistrationResponse,
    TenantSettingsResponse,
    TenantSettingsUpdate,
)
from app.modules.saas.service import (
    register_trial_tenant,
)


router = APIRouter()


@router.post(
    "/register",
    response_model=TenantRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a free trial account",
)
def register_tenant(
    payload: TenantRegistrationRequest,
    db: Session = Depends(get_db),
):
    """
    Creates a complete SaaS trial environment:

    - Tenant
    - Company
    - Main branch
    - Tenant owner user
    - Trial subscription
    - Enabled modules
    """

    return register_trial_tenant(
        db=db,
        payload=payload,
    )

def _require_settings_access(db: Session, current_user: User) -> int:
    tenant_id = get_effective_tenant_id(current_user)
    if current_user.is_platform_admin or current_user.is_superuser:
        if tenant_id is None:
            raise HTTPException(status_code=400, detail="Select a tenant before editing tenant settings")
        return tenant_id
    if current_user.tenant_id is None:
        raise HTTPException(status_code=403, detail="User is not assigned to a tenant")
    role = db.get(Role, current_user.role_id) if current_user.role_id else None
    if role is None or role.name not in {"Tenant Owner", "Tenant Admin", "Administrator"}:
        raise HTTPException(status_code=403, detail="Tenant settings require administrator access")
    return current_user.tenant_id


@router.get(
    "/settings",
    response_model=TenantSettingsResponse,
    summary="Get tenant workspace settings",
)
def get_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = get_effective_tenant_id(current_user)
    if tenant_id is None:
        raise HTTPException(status_code=403, detail="User is not assigned to a tenant")
    tenant = db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


@router.patch(
    "/settings",
    response_model=TenantSettingsResponse,
    summary="Update tenant workspace settings",
)
def update_settings(
    payload: TenantSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = _require_settings_access(db, current_user)
    tenant = db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")

    changes = payload.model_dump(exclude_unset=True)
    if "business_type" in changes and changes["business_type"] != tenant.business_type:
        if tenant.is_trial and not current_user.is_platform_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Business type cannot be changed during the free trial. Contact the platform administrator.",
            )

    for field, value in changes.items():
        setattr(tenant, field, value)

    if payload.default_language == "ar" and payload.default_locale is None:
        tenant.default_locale = "ar-EG"
    elif payload.default_language == "en" and payload.default_locale is None:
        tenant.default_locale = "en-US"

    db.commit()
    db.refresh(tenant)
    return tenant
