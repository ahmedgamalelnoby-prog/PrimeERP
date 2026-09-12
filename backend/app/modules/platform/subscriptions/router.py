from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user, get_current_user_for_billing
from app.modules.identity.models import User
from app.modules.platform.subscriptions.schemas import (
    SubscriptionConvertToPaid,
    SubscriptionCreate,
    SubscriptionResponse,
    SubscriptionUpdate,
)
from app.modules.platform.subscriptions.service import SubscriptionService


router = APIRouter(prefix="/subscriptions", tags=["Platform Subscriptions"])


def service(db: Session = Depends(get_db)) -> SubscriptionService:
    return SubscriptionService(db)


def authorize_tenant(tenant_id: int, current_user: User) -> None:
    if current_user.is_platform_admin:
        return
    if current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant access denied")


def require_platform_admin(current_user: User) -> None:
    if not current_user.is_platform_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform administrator access required")


@router.get("/tenant/{tenant_id}", response_model=List[SubscriptionResponse])
def list_subscriptions(
    tenant_id: int,
    current_user: User = Depends(get_current_user_for_billing),
    svc: SubscriptionService = Depends(service),
):
    authorize_tenant(tenant_id, current_user)
    return svc.list_for_tenant(tenant_id)


@router.get("/tenant/{tenant_id}/active", response_model=SubscriptionResponse)
def active_subscription(
    tenant_id: int,
    current_user: User = Depends(get_current_user_for_billing),
    svc: SubscriptionService = Depends(service),
):
    authorize_tenant(tenant_id, current_user)
    result = svc.get_active_for_tenant(tenant_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active subscription")
    return result


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
def get_subscription(
    subscription_id: int,
    current_user: User = Depends(get_current_user_for_billing),
    svc: SubscriptionService = Depends(service),
):
    try:
        subscription = svc._get(subscription_id)
        authorize_tenant(subscription.tenant_id, current_user)
        return subscription
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
def create_subscription(
    schema: SubscriptionCreate,
    current_user: User = Depends(get_current_user),
    svc: SubscriptionService = Depends(service),
):
    require_platform_admin(current_user)
    try:
        return svc.create(schema)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{subscription_id}/activate", response_model=SubscriptionResponse)
def activate_subscription(
    subscription_id: int,
    current_user: User = Depends(get_current_user),
    svc: SubscriptionService = Depends(service),
):
    require_platform_admin(current_user)
    try:
        return svc.activate(subscription_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{subscription_id}/convert-to-paid", response_model=SubscriptionResponse)
def convert_to_paid(
    subscription_id: int,
    schema: SubscriptionConvertToPaid,
    current_user: User = Depends(get_current_user_for_billing),
    svc: SubscriptionService = Depends(service),
):
    """Convert a tenant trial/past-due subscription into a paid subscription."""
    try:
        subscription = svc._get(subscription_id)
        authorize_tenant(subscription.tenant_id, current_user)
        return svc.convert_to_paid(subscription_id, schema)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{subscription_id}/cancel", response_model=SubscriptionResponse)
def cancel_subscription(
    subscription_id: int,
    reason: str = "customer_request",
    current_user: User = Depends(get_current_user_for_billing),
    svc: SubscriptionService = Depends(service),
):
    try:
        subscription = svc._get(subscription_id)
        authorize_tenant(subscription.tenant_id, current_user)
        return svc.cancel(subscription_id, reason)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/{subscription_id}", response_model=SubscriptionResponse)
def update_subscription(
    subscription_id: int,
    schema: SubscriptionUpdate,
    current_user: User = Depends(get_current_user),
    svc: SubscriptionService = Depends(service),
):
    require_platform_admin(current_user)
    try:
        return svc.update(subscription_id, schema)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
