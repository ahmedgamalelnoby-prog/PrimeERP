from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from app.database.base import Base
class DeveloperApp(Base):
    __tablename__="developer_apps"
    id=Column(Integer,primary_key=True);company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True);created_by=Column(Integer,ForeignKey("users.id",ondelete="SET NULL"));name=Column(String(160),nullable=False);client_id=Column(String(100),nullable=False);client_secret_hash=Column(String(128),nullable=False);redirect_uris=Column(JSON,nullable=False,server_default="[]");scopes=Column(JSON,nullable=False,server_default="[]");is_active=Column(Boolean,nullable=False,server_default="true");created_at=Column(DateTime,nullable=False,server_default=func.now());rotated_at=Column(DateTime)
    __table_args__=(UniqueConstraint("company_id","client_id",name="uq_developer_app_company_client"),)
class DeveloperApiKey(Base):
    __tablename__="developer_api_keys"
    id=Column(Integer,primary_key=True);app_id=Column(Integer,ForeignKey("developer_apps.id",ondelete="CASCADE"),nullable=False,index=True);key_prefix=Column(String(24),nullable=False);key_hash=Column(String(128),nullable=False);scopes=Column(JSON,nullable=False,server_default="[]");expires_at=Column(DateTime);last_used_at=Column(DateTime);revoked_at=Column(DateTime);created_at=Column(DateTime,nullable=False,server_default=func.now())
    __table_args__=(UniqueConstraint("app_id","key_hash",name="uq_developer_key_hash"),)
class DeveloperWebhook(Base):
    __tablename__="developer_webhooks"
    id=Column(Integer,primary_key=True);app_id=Column(Integer,ForeignKey("developer_apps.id",ondelete="CASCADE"),nullable=False,index=True);url=Column(String(1000),nullable=False);secret_hash=Column(String(128),nullable=False);secret_encrypted=Column(Text,nullable=False);events=Column(JSON,nullable=False,server_default="[]");is_active=Column(Boolean,nullable=False,server_default="true");created_at=Column(DateTime,nullable=False,server_default=func.now())
class DeveloperWebhookDelivery(Base):
    __tablename__="developer_webhook_deliveries"
    id=Column(Integer,primary_key=True);webhook_id=Column(Integer,ForeignKey("developer_webhooks.id",ondelete="CASCADE"),nullable=False,index=True);event_id=Column(String(160),nullable=False);event_type=Column(String(160),nullable=False);payload=Column(JSON,nullable=False);status=Column(String(20),nullable=False,server_default="pending");attempts=Column(Integer,nullable=False,server_default="0");response_code=Column(Integer);response_body=Column(Text);next_attempt_at=Column(DateTime);delivered_at=Column(DateTime);created_at=Column(DateTime,nullable=False,server_default=func.now())
    __table_args__=(UniqueConstraint("webhook_id","event_id",name="uq_developer_webhook_event"),CheckConstraint("status IN ('pending','delivered','failed','disabled')",name="ck_developer_delivery_status"),)
class DeveloperEvent(Base):
    __tablename__="developer_events"
    id=Column(Integer,primary_key=True);company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True);event_id=Column(String(160),nullable=False);event_type=Column(String(160),nullable=False);payload=Column(JSON,nullable=False);created_at=Column(DateTime,nullable=False,server_default=func.now())
    __table_args__=(UniqueConstraint("company_id","event_id",name="uq_developer_event_company"),)
class DeveloperCustomField(Base):
    __tablename__="developer_custom_fields"
    id=Column(Integer,primary_key=True);company_id=Column(Integer,ForeignKey("companies.id",ondelete="CASCADE"),nullable=False,index=True);entity_type=Column(String(80),nullable=False);field_key=Column(String(100),nullable=False);label=Column(String(160),nullable=False);field_type=Column(String(30),nullable=False);required=Column(Boolean,nullable=False,server_default="false");options=Column(JSON,nullable=False,server_default="[]");is_active=Column(Boolean,nullable=False,server_default="true")
    __table_args__=(UniqueConstraint("company_id","entity_type","field_key",name="uq_developer_custom_field"),)
