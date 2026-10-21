from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.context import get_effective_tenant_id
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.inventory.locations.schemas import LocationCreate, LocationResponse, LocationUpdate
from app.modules.inventory.locations.service import location_service
from app.modules.saas.entitlements import require_module

router = APIRouter(prefix="/inventory/locations", tags=["Inventory - Locations"], dependencies=[Depends(require_module("inventory"))])


def _company_for_user(db: Session, company_id: int, user: User):
    if get_effective_tenant_id(user) is None: raise HTTPException(403, "User is not assigned to a tenant")
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == get_effective_tenant_id(user)))
    if company is None: raise HTTPException(403, "Company is outside the current tenant")
    return company


@router.get("", response_model=list[LocationResponse], dependencies=[Depends(require_permission("inventory.access"))])
def list_locations(company_id: int = Query(gt=0), warehouse_id: int = Query(gt=0), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, user)
    try: return location_service.list(db, company_id=company_id, warehouse_id=warehouse_id)
    except ValueError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("", response_model=LocationResponse, status_code=201, dependencies=[Depends(require_permission("inventory.write"))])
def create_location(payload: LocationCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _company_for_user(db, payload.company_id, user)
    try: return location_service.create(db, payload=payload)
    except ValueError as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.patch("/{location_id}", response_model=LocationResponse, dependencies=[Depends(require_permission("inventory.write"))])
def update_location(location_id: int, payload: LocationUpdate, company_id: int = Query(gt=0), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, user)
    try: return location_service.update(db, company_id=company_id, location_id=location_id, payload=payload)
    except ValueError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
