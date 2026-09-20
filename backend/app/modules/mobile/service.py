from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.modules.mobile.models import MobileDevice, MobileSyncOperation, MobileScanEvent, MobileSession, MobileTask

def register_device(db: Session, user, p):
    c = db.scalar(select(MobileDevice).where(
        MobileDevice.company_id == p.company_id,
        MobileDevice.device_uid == p.device_uid,
    ))
    if c:
        if c.user_id != user.id:
            raise HTTPException(403, "Device belongs to another user")
        c.name = p.name
        c.platform = p.platform
        c.app_version = p.app_version
        c.last_seen_at = datetime.now(timezone.utc)
        c.is_active = True
    else:
        c = MobileDevice(
            company_id=p.company_id, user_id=user.id, device_uid=p.device_uid,
            name=p.name, platform=p.platform, app_version=p.app_version,
            last_seen_at=datetime.now(timezone.utc), is_active=True,
        )
        db.add(c)
    db.commit()
    db.refresh(c)
    return c

def _process_operation(db: Session, device: MobileDevice, user, item):
    now = datetime.now(timezone.utc)
    if item.operation_type == "scan":
        payload = item.payload or {}
        session_id = payload.get("session_id")
        barcode = payload.get("barcode")
        context = payload.get("context", "inventory")
        if not session_id or not barcode:
            raise HTTPException(422, "scan requires session_id and barcode")
        session = db.scalar(select(MobileSession).where(
            MobileSession.id == session_id,
            MobileSession.device_id == device.id,
            MobileSession.user_id == user.id,
            MobileSession.status == "open",
        ))
        if not session:
            raise HTTPException(409, "Scan session is not open or does not belong to this device")
        scan = MobileScanEvent(
            company_id=device.company_id, device_id=device.id, session_id=session.id,
            barcode=str(barcode), symbology=payload.get("symbology"),
            context=str(context), payload=payload,
        )
        db.add(scan)
        db.flush()
        return {"accepted": True, "scan_id": scan.id, "operation_type": item.operation_type}
    if item.operation_type == "task.complete":
        task_id = (item.payload or {}).get("task_id")
        if not task_id:
            raise HTTPException(422, "task.complete requires task_id")
        task = db.scalar(select(MobileTask).where(
            MobileTask.id == task_id,
            MobileTask.company_id == device.company_id,
            MobileTask.assigned_user_id == user.id,
        ))
        if not task:
            raise HTTPException(404, "Task not found")
        if task.status not in ("open", "in_progress"):
            raise HTTPException(409, "Task cannot be completed")
        task.status = "completed"
        task.completed_at = now
        return {"accepted": True, "task_id": task.id, "status": task.status, "operation_type": item.operation_type}
    raise HTTPException(422, f"Unsupported mobile operation type: {item.operation_type}")

def sync(db: Session, user, p):
    d = db.scalar(select(MobileDevice).where(
        MobileDevice.id == p.device_id,
        MobileDevice.user_id == user.id,
        MobileDevice.is_active.is_(True),
    ))
    if not d:
        raise HTTPException(404, "Mobile device not found")

    results = []
    for item in p.operations:
        existing = db.scalar(select(MobileSyncOperation).where(
            MobileSyncOperation.company_id == d.company_id,
            MobileSyncOperation.operation_id == item.operation_id,
        ))
        if existing:
            results.append({
                "operation_id": item.operation_id,
                "status": existing.status,
                "result": existing.result,
                "error": existing.error,
            })
            continue
        row = MobileSyncOperation(
            company_id=d.company_id, device_id=d.id,
            operation_id=item.operation_id, operation_type=item.operation_type,
            payload=item.payload, status="accepted",
        )
        db.add(row)
        try:
            row.result = _process_operation(db, d, user, item)
            row.status = "processed"
            row.processed_at = datetime.now(timezone.utc)
        except HTTPException as exc:
            row.status = "failed"
            row.error = str(exc.detail)
            row.result = {"accepted": False}
        except Exception as exc:
            row.status = "failed"
            row.error = str(exc)[:2000]
            row.result = {"accepted": False}
        results.append({
            "operation_id": item.operation_id,
            "status": row.status,
            "result": row.result,
            "error": row.error,
        })
    d.last_seen_at = datetime.now(timezone.utc)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        for item in p.operations:
            existing = db.scalar(select(MobileSyncOperation).where(
                MobileSyncOperation.company_id == d.company_id,
                MobileSyncOperation.operation_id == item.operation_id,
            ))
            if existing:
                results = [x for x in results if x["operation_id"] != item.operation_id]
                results.append({
                    "operation_id": item.operation_id,
                    "status": existing.status,
                    "result": existing.result,
                    "error": existing.error,
                })
        db.commit()
    return results
