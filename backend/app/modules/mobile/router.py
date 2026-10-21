from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.context import get_effective_tenant_id
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.mobile.models import MobileDevice,MobileSession,MobileTask,MobileScanEvent
from app.modules.mobile.schemas import *
from app.modules.mobile.service import register_device,sync
from app.modules.inventory.warehouses.models import InventoryWarehouse
from app.modules.branches.models import Branch
router=APIRouter(prefix="/mobile",tags=["Mobile Execution"])

def company_ok(db,company_id,user):
    from app.modules.companies.models import Company
    tenant_id = get_effective_tenant_id(user)
    if tenant_id is None: raise HTTPException(403,"User is not assigned to a tenant")
    if not db.scalar(select(Company.id).where(Company.id==company_id,Company.tenant_id==tenant_id,Company.is_active.is_(True))): raise HTTPException(404,"Company not found")
    return tenant_id

@router.post("/devices",response_model=DeviceResponse,dependencies=[Depends(require_permission("mobile.write"))])
def devices(p:DeviceRegister,db:Session=Depends(get_db),user:User=Depends(get_current_user)): company_ok(db,p.company_id,user);return register_device(db,user,p)

@router.get("/devices",response_model=list[DeviceResponse],dependencies=[Depends(require_permission("mobile.access"))])
def list_devices(company_id:int=Query(...,gt=0),db:Session=Depends(get_db),user:User=Depends(get_current_user)): company_ok(db,company_id,user);return list(db.scalars(select(MobileDevice).where(MobileDevice.company_id==company_id,MobileDevice.user_id==user.id).order_by(MobileDevice.id.desc())).all())

@router.post("/sessions",response_model=SessionResponse,dependencies=[Depends(require_permission("mobile.write"))])
def open_session(p:SessionCreate,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    d=db.scalar(select(MobileDevice).where(MobileDevice.id==p.device_id,MobileDevice.user_id==user.id,MobileDevice.is_active.is_(True)))
    if not d: raise HTTPException(404,"Device not found")
    old=db.scalar(select(MobileSession).where(MobileSession.device_id==d.id,MobileSession.status=="open"))
    if old: old.status="closed";old.closed_at=datetime.now(timezone.utc)
    if p.warehouse_id and not db.scalar(select(InventoryWarehouse.id).where(InventoryWarehouse.id==p.warehouse_id,InventoryWarehouse.company_id==d.company_id,InventoryWarehouse.is_active.is_(True))): raise HTTPException(404,"Warehouse not found")
    if p.branch_id and not db.scalar(select(Branch.id).where(Branch.id==p.branch_id,Branch.company_id==d.company_id)): raise HTTPException(404,"Branch not found")
    s=MobileSession(device_id=d.id,user_id=user.id,warehouse_id=p.warehouse_id,branch_id=p.branch_id);db.add(s);db.commit();db.refresh(s);return s

@router.post("/sessions/{session_id}/close",response_model=SessionResponse,dependencies=[Depends(require_permission("mobile.write"))])
def close_session(session_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    s=db.scalar(select(MobileSession).where(MobileSession.id==session_id,MobileSession.user_id==user.id))
    if not s: raise HTTPException(404,"Session not found")
    if s.status!="open": raise HTTPException(409,"Session is not open")
    s.status="closed";s.closed_at=datetime.now(timezone.utc);db.commit();db.refresh(s);return s

@router.post("/sync",dependencies=[Depends(require_permission("mobile.write"))])
def sync_batch(p:SyncBatch,db:Session=Depends(get_db),user:User=Depends(get_current_user)): return {"items":sync(db,user,p)}

@router.get("/tasks",response_model=list[TaskResponse],dependencies=[Depends(require_permission("mobile.access"))])
def tasks(company_id:int=Query(...,gt=0),status:str|None=None,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    company_ok(db,company_id,user);q=select(MobileTask).where(MobileTask.company_id==company_id,(MobileTask.assigned_user_id==user.id)|(MobileTask.assigned_user_id.is_(None)))
    if status:q=q.where(MobileTask.status==status)
    return list(db.scalars(q.order_by(MobileTask.id.desc())).all())

@router.post("/tasks",response_model=TaskResponse,status_code=201,dependencies=[Depends(require_permission("mobile.write"))])
def create_task(p:TaskCreate,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    company_ok(db,p.company_id,user)
    tenant_id = get_effective_tenant_id(user)
    if p.assigned_user_id and not db.scalar(select(User.id).where(User.id==p.assigned_user_id,User.tenant_id==tenant_id,User.is_deleted.is_(False))): raise HTTPException(422,"Assigned user is outside the tenant")
    t=MobileTask(**p.model_dump());db.add(t);db.commit();db.refresh(t);return t

@router.post("/tasks/{task_id}/complete",response_model=TaskResponse,dependencies=[Depends(require_permission("mobile.write"))])
def complete_task(task_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    t=db.scalar(select(MobileTask).where(MobileTask.id==task_id,MobileTask.assigned_user_id==user.id))
    if not t: raise HTTPException(404,"Task not found")
    if t.status not in ("open","in_progress"): raise HTTPException(409,"Task cannot be completed")
    t.status="completed";t.completed_at=datetime.now(timezone.utc);db.commit();db.refresh(t);return t

@router.post("/scans",response_model=ScanResponse,status_code=201,dependencies=[Depends(require_permission("mobile.write"))])
def scan(p:ScanCreate,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    s=db.scalar(select(MobileSession).where(MobileSession.id==p.session_id,MobileSession.user_id==user.id,MobileSession.status=="open"))
    if not s: raise HTTPException(404,"Open mobile session not found")
    company_id=db.scalar(select(MobileDevice.company_id).where(MobileDevice.id==s.device_id));row=MobileScanEvent(company_id=company_id,device_id=s.device_id,session_id=s.id,**p.model_dump());db.add(row);db.commit();db.refresh(row);return row
