from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.database.base import Base


class ReportSchedule(Base):
    __tablename__ = "report_schedules"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(160), nullable=False)
    report_key = Column(String(80), nullable=False)
    frequency = Column(String(20), nullable=False, server_default="monthly")
    cron = Column(String(120), nullable=True)
    timezone = Column(String(80), nullable=False, server_default="Africa/Cairo")
    channels = Column(Text, nullable=False, server_default='["email"]')
    recipients = Column(Text, nullable=False, server_default="[]")
    filters = Column(Text, nullable=False, server_default="{}")
    format = Column(String(20), nullable=False, server_default="csv")
    include_ai = Column(Boolean, nullable=False, server_default="true")
    is_active = Column(Boolean, nullable=False, server_default="true")
    next_run_at = Column(DateTime(timezone=True), nullable=True, index=True)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class ReportDeliveryLog(Base):
    __tablename__ = "report_delivery_logs"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    schedule_id = Column(Integer, ForeignKey("report_schedules.id", ondelete="SET NULL"), nullable=True, index=True)
    report_key = Column(String(80), nullable=False)
    channel = Column(String(20), nullable=False)
    recipient = Column(String(320), nullable=False)
    status = Column(String(20), nullable=False)
    provider_message_id = Column(String(200), nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
