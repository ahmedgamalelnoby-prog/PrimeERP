from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.platform.subscriptions.schemas import SubscriptionCreate, SubscriptionResponse, SubscriptionUpdate
from app.modules.platform.subscriptions.service import SubscriptionService

router = APIRouter(prefix="/subscriptions", tags=["Platform Subscriptions"])


def service(db: Session = Depends(get_db)) -> SubscriptionService:
    return SubscriptionService(db)


@router.get("/tenant/{tenant_id}", response_model=List[SubscriptionResponse])
def list_subscriptions(tenant_id: int, svc: SubscriptionService = Depends(service)):
    return svc.list_for_tenant(tenant_id)


@router.get("/tenant/{tenant_id}/active", response_model=SubscriptionResponse)
def active_subscription(tenant_id: int, svc: SubscriptionService = Depends(service)):
    result = svc.get_active_for_tenant(tenant_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active subscription")
    return result


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
def get_subscription(subscription_id: int, svc: SubscriptionService = Depends(service)):
    try:
        return svc._get(subscription_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
def create_subscription(schema: SubscriptionCreate, svc: SubscriptionService = Depends(service)):
    try:
        return svc.create(schema)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{subscription_id}/activate", response_model=SubscriptionResponse)
def activate_subscription(subscription_id: int, svc: SubscriptionService = Depends(service)):
    try:
        return svc.activate(subscription_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{subscription_id}/cancel", response_model=SubscriptionResponse)
def cancel_subscription(subscription_id: int, reason: str = "customer_request", svc: SubscriptionService = Depends(service)):
    try:
        return svc.cancel(subscription_id, reason)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/{subscription_id}", response_model=SubscriptionResponse)
def update_subscription(subscription_id: int, schema: SubscriptionUpdate, svc: SubscriptionService = Depends(service)):
    try:
        return svc.update(subscription_id, schema)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
