from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.identity.dependencies.current_user import get_current_user
from app.modules.identity.models import User
from .service import completion_service

router = APIRouter(prefix="/completion", tags=["Enterprise Completion"])


@router.post("/periods/{company_id}/{period_key}/lock")
def lock_period(
    company_id: int,
    period_key: str,
    module: str = "*",
    reason: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Privileged accounting administrator is required")
    if current_user.tenant_id is None:
        raise HTTPException(status_code=403, detail="Tenant context is required")
    return completion_service.lock_period(
        db,
        company_id,
        period_key,
        module,
        reason,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
    )
