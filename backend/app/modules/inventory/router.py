from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from .schemas import WarehouseCreate,WarehouseRead,LocationCreate,LocationRead,MovementCreate,TransferCreate,ReservationCreate,IssueCreate
from .service import inventory_service
router=APIRouter(prefix="/inventory",tags=["inventory"])
def _tenant(user:User)->int:
    if user.is_platform_admin or user.tenant_id is None: raise HTTPException(403,"Active tenant context is required")
    return user.tenant_id
@router.get("/warehouses",response_model=list[WarehouseRead])
def warehouses(db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return inventory_service.list_warehouses(db,_tenant(current_user))
@router.post("/warehouses",response_model=WarehouseRead,status_code=201)
def create_warehouse(payload:WarehouseCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return inventory_service.create_warehouse(db,_tenant(current_user),payload)
@router.get("/warehouses/{warehouse_id}/locations",response_model=list[LocationRead])
def locations(warehouse_id:int,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return inventory_service.list_locations(db,_tenant(current_user),warehouse_id)
@router.post("/locations",response_model=LocationRead,status_code=201)
def create_location(payload:LocationCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return inventory_service.create_location(db,_tenant(current_user),payload)
@router.get("/balances")
def balances(warehouse_id:int|None=Query(None),product_id:int|None=Query(None),db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    rows=inventory_service.list_balances(db,_tenant(current_user),warehouse_id,product_id)
    return [{"id":r.id,"warehouse_id":r.warehouse_id,"location_id":r.location_id,"product_id":r.product_id,"quantity":r.quantity,"reserved_quantity":r.reserved_quantity,"available_quantity":r.quantity-r.reserved_quantity} for r in rows]
@router.post("/movements",status_code=201)
def movement(payload:MovementCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return inventory_service.post_movement(db,_tenant(current_user),payload)
@router.post("/transfers",status_code=201)
def transfer(payload:TransferCreate,status_code:int=201,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return inventory_service.post_transfer(db,_tenant(current_user),payload)
@router.post("/reservations",status_code=201)
def reservation(payload:ReservationCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return inventory_service.reserve(db,_tenant(current_user),payload)
@router.post("/issues",status_code=201)
def issue(payload:IssueCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return inventory_service.issue(db,_tenant(current_user),payload)

@router.post("/reservations/{reservation_id}/release")
def release_reservation(reservation_id:int,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    return inventory_service.release_reservation(db,_tenant(current_user),reservation_id)
