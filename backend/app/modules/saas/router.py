from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.saas.schemas import TenantRegistrationRequest, TenantRegistrationResponse
from app.modules.saas.service_v2 import register_trial_tenant

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
    return register_trial_tenant(db=db, payload=payload)
