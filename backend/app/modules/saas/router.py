from fastapi import (
    APIRouter,
    Depends,
    status,
)
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.saas.models import SystemModule
from app.modules.saas.schemas import (
    SystemModuleResponse,
    TenantRegistrationRequest,
    TenantRegistrationResponse,
)
from app.modules.saas.service import (
    register_trial_tenant,
)


router = APIRouter()


@router.get(
    "/modules/catalog",
    response_model=list[SystemModuleResponse],
    summary="List available ERP applications",
)
def list_module_catalog(
    db: Session = Depends(get_db),
):
    """Return the active PrimeERP application catalog.

    The catalog is intentionally independent from tenant entitlements: it is the
    master list of applications that can be priced, enabled, or implemented.
    """
    return (
        db.query(SystemModule)
        .filter(SystemModule.is_active.is_(True))
        .order_by(SystemModule.display_order.asc(), SystemModule.id.asc())
        .all()
    )


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
