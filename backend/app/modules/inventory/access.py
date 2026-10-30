from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import HTTPException

from app.core.context import get_effective_tenant_id
from app.modules.branches.access import accessible_branch_ids, can_manage_all_branches, require_branch_access
from app.modules.inventory.locations.models import InventoryLocation
from app.modules.inventory.warehouses.models import InventoryWarehouse
from app.modules.identity.models import User


def require_warehouse_access(
    db: Session,
    user: User,
    company_id: int,
    warehouse_id: int,
) -> InventoryWarehouse:
    warehouse = db.scalar(
        select(InventoryWarehouse).where(
            InventoryWarehouse.id == warehouse_id,
            InventoryWarehouse.company_id == company_id,
            InventoryWarehouse.tenant_id == get_effective_tenant_id(user),
            InventoryWarehouse.is_active.is_(True),
        )
    )
    if warehouse is None:
        raise HTTPException(status_code=404, detail="Warehouse not found for company")
    if warehouse.branch_id is None:
        if not can_manage_all_branches(db, user):
            raise HTTPException(
                status_code=403,
                detail="Central warehouse access requires tenant-wide branch management permission",
            )
    else:
        branch = require_branch_access(db, user, warehouse.branch_id)
        if branch.company_id != company_id:
            raise HTTPException(status_code=404, detail="Warehouse not found for company")
    return warehouse


def require_location_access(
    db: Session,
    user: User,
    company_id: int,
    location_id: int,
) -> InventoryLocation:
    location = db.scalar(
        select(InventoryLocation).where(
            InventoryLocation.id == location_id,
            InventoryLocation.company_id == company_id,
            InventoryLocation.is_active.is_(True),
        )
    )
    if location is None:
        raise HTTPException(status_code=404, detail="Location not found for company")
    require_warehouse_access(db, user, company_id, location.warehouse_id)
    return location


def accessible_warehouse_ids(
    db: Session,
    user: User,
    company_id: int,
) -> set[int] | None:
    if can_manage_all_branches(db, user):
        return None
    branch_ids = accessible_branch_ids(db, user)
    if not branch_ids:
        return set()
    return set(
        db.scalars(
            select(InventoryWarehouse.id).where(
                InventoryWarehouse.company_id == company_id,
                InventoryWarehouse.tenant_id == get_effective_tenant_id(user),
                InventoryWarehouse.branch_id.in_(branch_ids),
                InventoryWarehouse.is_active.is_(True),
            )
        ).all()
    )
