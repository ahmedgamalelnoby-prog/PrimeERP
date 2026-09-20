from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.modules.mobile.models import MobileDevice, MobileSyncOperation

def register_device(db:Session,user,p):
    c=db.scalar(select(MobileDevice).where(MobileDevice.company_id==p.company_id,MobileDevice.device_uid==p.device_uid))
    if c:
        if c.user_id!=user.id: raise HTTPException(403,"Device belongs to another user")
        c.name=p.name;c.platform=p.platform;c.app_version=p.app_version;c.last_seen_at=datetime.now(timezone.utc);c.is_active=True
    else:
        c=MobileDevice(company_id=p.company_id,user_id=user.id,device_uid=p.device_uid,name=p.name,platform=p.platform,app_version=p.app_version,last_seen_at=datetime.now(timezone.utc),is_active=True);db.add(c)
    db.commit();db.refresh(c);return c

def sync(db:Session,user,p):
    d=db.scalar(select(MobileDevice).where(MobileDevice.id==p.device_id,MobileDevice.user_id==user.id,MobileDevice.is_active.is_(True)))
    if not d: raise HTTPException(404,"Mobile device not found")
    results=[]
    for item in p.operations:
        existing=db.scalar(select(MobileSyncOperation).where(MobileSyncOperation.company_id==d.company_id,MobileSyncOperation.operation_id==item.operation_id))
        if existing: results.append({"operation_id":item.operation_id,"status":existing.status,"result":existing.result});continue
        row=MobileSyncOperation(company_id=d.company_id,device_id=d.id,operation_id=item.operation_id,operation_type=item.operation_type,payload=item.payload,status="processed",result={"accepted":True,"operation_type":item.operation_type},processed_at=datetime.now(timezone.utc));db.add(row)
        results.append({"operation_id":item.operation_id,"status":"processed","result":row.result})
    d.last_seen_at=datetime.now(timezone.utc);db.commit();return results
