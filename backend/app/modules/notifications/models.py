from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from app.database.base import Base


class NotificationTemplate(Base):
    __tablename__ = "notification_templates"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(80), nullable=False)
    channel = Column(String(20), nullable=False)
    title_template = Column(String(255), nullable=False, default="")
    body_template = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    __table_args__ = (
        UniqueConstraint("company_id", "code", "channel", name="uq_notification_template_company_code_channel"),
    )


class NotificationGroup(Base):
    __tablename__ = "notification_groups"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(80), nullable=False)
    name = Column(String(160), nullable=False)
    channel = Column(String(20), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_notification_group_company_code"),
    )


class NotificationGroupMember(Base):
    __tablename__ = "notification_group_members"
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("notification_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    destination = Column(String(320), nullable=False)
    label = Column(String(160), nullable=False, default="")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    __table_args__ = (UniqueConstraint("group_id", "destination", name="uq_notification_group_member_destination"),)


class NotificationDelivery(Base):
    __tablename__ = "notification_deliveries"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    channel = Column(String(20), nullable=False)
    destination = Column(String(320), nullable=False)
    title = Column(String(255), nullable=False, default="")
    body = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="queued")
    provider_reference = Column(String(255), nullable=True)
    error_code = Column(String(80), nullable=True)
    idempotency_key = Column(String(120), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    __table_args__ = (
        UniqueConstraint("company_id", "idempotency_key", name="uq_notification_delivery_company_idempotency"),
    )
