from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from app.database.base import Base

class MobileDevice(Base):
    __tablename__="mobile_devices"
    id=Column(Integer,primary_key=True); company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True); user_id=Column(Integer,ForeignKey("users.id",ondelete="CASCADE"),nullable=False,index=True)
    device_uid=Column(String(160),nullable=False); name=Column(String(160),nullable=False); platform=Column(String(30),nullable=False); app_version=Column(String(40)); last_seen_at=Column(DateTime); is_active=Column(Boolean,nullable=False,server_default="true"); created_at=Column(DateTime,nullable=False,server_default=func.now())
    __table_args__=(UniqueConstraint("company_id","device_uid",name="uq_mobile_device_company_uid"),)

class MobileSession(Base):
    __tablename__="mobile_sessions"
    id=Column(Integer,primary_key=True); device_id=Column(Integer,ForeignKey("mobile_devices.id",ondelete="CASCADE"),nullable=False,index=True); user_id=Column(Integer,ForeignKey("users.id",ondelete="CASCADE"),nullable=False,index=True); warehouse_id=Column(Integer,ForeignKey("inventory_warehouses.id",ondelete="SET NULL")); branch_id=Column(Integer,ForeignKey("branches.id",ondelete="SET NULL")); status=Column(String(20),nullable=False,server_default="open"); opened_at=Column(DateTime,nullable=False,server_default=func.now()); closed_at=Column(DateTime)
    __table_args__=(CheckConstraint("status IN ('open','closed','expired')",name="ck_mobile_session_status"),)

class MobileSyncOperation(Base):
    __tablename__="mobile_sync_operations"
    id=Column(Integer,primary_key=True); company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True); device_id=Column(Integer,ForeignKey("mobile_devices.id",ondelete="CASCADE"),nullable=False,index=True); operation_id=Column(String(160),nullable=False); operation_type=Column(String(80),nullable=False); payload=Column(JSON,nullable=False); status=Column(String(20),nullable=False,server_default="accepted"); result=Column(JSON); error=Column(Text); created_at=Column(DateTime,nullable=False,server_default=func.now()); processed_at=Column(DateTime)
    __table_args__=(UniqueConstraint("company_id","operation_id",name="uq_mobile_sync_company_operation"),CheckConstraint("status IN ('accepted','processed','failed')",name="ck_mobile_sync_status"),)

class MobileTask(Base):
    __tablename__="mobile_tasks"
    id=Column(Integer,primary_key=True); company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True); assigned_user_id=Column(Integer,ForeignKey("users.id",ondelete="SET NULL"),index=True); task_type=Column(String(60),nullable=False); reference_type=Column(String(60)); reference_id=Column(Integer); title=Column(String(200),nullable=False); payload=Column(JSON,nullable=False,server_default="{}"); status=Column(String(20),nullable=False,server_default="open"); due_at=Column(DateTime); completed_at=Column(DateTime)
    __table_args__=(CheckConstraint("status IN ('open','in_progress','completed','cancelled')",name="ck_mobile_task_status"),)

class MobileScanEvent(Base):
    __tablename__="mobile_scan_events"
    id=Column(Integer,primary_key=True); company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True); device_id=Column(Integer,ForeignKey("mobile_devices.id",ondelete="CASCADE"),nullable=False,index=True); session_id=Column(Integer,ForeignKey("mobile_sessions.id",ondelete="CASCADE"),nullable=False,index=True); barcode=Column(String(160),nullable=False,index=True); symbology=Column(String(40)); context=Column(String(60),nullable=False); payload=Column(JSON); scanned_at=Column(DateTime,nullable=False,server_default=func.now())
