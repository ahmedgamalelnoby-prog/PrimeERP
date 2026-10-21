from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.context import get_effective_tenant_id
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.company_settings.service import get_company_setting
from app.modules.catalog.service import catalog_service
from app.modules.inventory.stock_moves.schemas import StockMoveCreate
from app.modules.inventory.stock_moves.service import inventory_stock_move_service
from app.modules.manufacturing.production_orders.schemas import WorkOrderComplete, WorkOrderCreate, WorkOrderResponse
from app.modules.manufacturing.production_orders.service import manufacturing_work_order_service
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models.user import User
from app.modules.saas.entitlements import require_module

router = APIRouter(
    prefix="/manufacturing",
    tags=["Manufacturing"],
    dependencies=[
        Depends(require_permission("inventory.access")),
        Depends(require_module("manufacturing")),
        Depends(require_module("inventory")),
    ],
)


class MaterialIssue(BaseModel):
    company_id: int = Field(gt=0)
    item_id: int = Field(gt=0)
    source_location_id: int = Field(gt=0)
    quantity: Decimal = Field(gt=0)
    reference: str = Field(min_length=1, max_length=100)


def _company(db: Session, company_id: int, user: User) -> int:
    tenant_id = get_effective_tenant_id(user)
    if tenant_id is None:
        raise HTTPException(403, "User is not assigned to a tenant")
    company = db.scalar(
        select(Company).where(
            Company.id == company_id,
            Company.tenant_id == tenant_id,
            Company.is_active.is_(True),
        )
    )
    if company is None:
        raise HTTPException(403, "Company is outside the current tenant")
    return tenant_id


@router.get("/bom")
def list_bom(
    company_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _company(db, company_id, current_user)
    return catalog_service.list_recipes(db, company_id)


@router.get("/bom/{recipe_id}")
def get_bom(
    recipe_id: int,
    company_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _company(db, company_id, current_user)
    return catalog_service.get_recipe(db, company_id, recipe_id)


@router.post(
    "/material-issues",
    dependencies=[
        Depends(require_permission("inventory.write")),
        Depends(require_permission("inventory.post")),
    ],
)
def issue_material(
    payload: MaterialIssue,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tenant_id = _company(db, payload.company_id, current_user)
    if get_company_setting(db, payload.company_id, "manufacturing.require_work_order") is True:
        raise HTTPException(409, "Company policy requires material consumption to be completed through a released work order")
    move = inventory_stock_move_service.create_draft(
        db,
        StockMoveCreate(
            company_id=payload.company_id,
            item_id=payload.item_id,
            source_location_id=payload.source_location_id,
            quantity=payload.quantity,
            unit_cost=0,
            movement_type="issue",
            reference=payload.reference,
            source_module="manufacturing",
            source_entity="material_issue",
            source_id=payload.reference,
        ),
    )
    inventory_stock_move_service.post(
        db,
        tenant_id=tenant_id,
        company_id=payload.company_id,
        move_id=move.id,
        user_id=current_user.id,
    )
    db.commit()
    db.refresh(move)
    return move


def _commit_work_order(db: Session, action):
    try:
        result = action()
        db.commit()
        db.refresh(result)
        return result
    except ValueError as exc:
        db.rollback()
        raise HTTPException(409, str(exc)) from exc
    except Exception:
        db.rollback()
        raise


@router.get("/work-orders", response_model=list[WorkOrderResponse])
def list_work_orders(
    company_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _company(db, company_id, current_user)
    return manufacturing_work_order_service.list(db, company_id=company_id)


@router.post(
    "/work-orders",
    response_model=WorkOrderResponse,
    status_code=201,
    dependencies=[Depends(require_permission("inventory.write"))],
)
def create_work_order(
    payload: WorkOrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _company(db, payload.company_id, current_user)
    return _commit_work_order(
        db,
        lambda: manufacturing_work_order_service.create(
            db, payload=payload, user_id=current_user.id
        ),
    )


@router.post(
    "/work-orders/{work_order_id}/release",
    response_model=WorkOrderResponse,
    dependencies=[Depends(require_permission("inventory.write"))],
)
def release_work_order(
    work_order_id: int,
    company_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _company(db, company_id, current_user)
    return _commit_work_order(
        db,
        lambda: manufacturing_work_order_service.release(
            db, company_id=company_id, work_order_id=work_order_id, user_id=current_user.id
        ),
    )


@router.post(
    "/work-orders/{work_order_id}/complete",
    response_model=WorkOrderResponse,
    dependencies=[Depends(require_permission("inventory.post"))],
)
def complete_work_order(
    work_order_id: int,
    payload: WorkOrderComplete,
    company_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tenant_id = _company(db, company_id, current_user)
    return _commit_work_order(
        db,
        lambda: manufacturing_work_order_service.complete(
            db,
            tenant_id=tenant_id,
            company_id=company_id,
            work_order_id=work_order_id,
            produced_quantity=payload.produced_quantity,
            user_id=current_user.id,
        ),
    )


@router.post(
    "/work-orders/{work_order_id}/cancel",
    response_model=WorkOrderResponse,
    dependencies=[Depends(require_permission("inventory.post"))],
)
def cancel_work_order(
    work_order_id: int,
    company_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tenant_id = _company(db, company_id, current_user)
    return _commit_work_order(
        db,
        lambda: manufacturing_work_order_service.cancel(
            db,
            tenant_id=tenant_id,
            company_id=company_id,
            work_order_id=work_order_id,
            user_id=current_user.id,
        ),
    )
