from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from app.database.base import Base


class ReportDefinition(Base):
    __tablename__ = "report_definitions"
    __table_args__ = (UniqueConstraint("company_id", "code", name="uq_report_definitions_company_code"),)

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    report_type = Column(String(50), nullable=False, default="custom")
    parameters_json = Column(Text, nullable=False, default="{}")
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class ReportDelivery(Base):
    __tablename__ = "report_deliveries"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    report_definition_id = Column(Integer, ForeignKey("report_definitions.id", ondelete="CASCADE"), nullable=False, index=True)
    channel = Column(String(30), nullable=False)
    destination = Column(String(320), nullable=False)
    schedule = Column(String(120), nullable=False)
    format = Column(String(20), nullable=False, default="json")
    filters_json = Column(Text, nullable=False, default="{}")
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True, index=True)
    last_status = Column(String(30), nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class ReportDeliveryAttempt(Base):
    __tablename__ = "report_delivery_attempts"
    __table_args__ = (UniqueConstraint("delivery_id", "attempt_no", name="uq_report_delivery_attempt_no"),)

    id = Column(Integer, primary_key=True)
    delivery_id = Column(Integer, ForeignKey("report_deliveries.id", ondelete="CASCADE"), nullable=False, index=True)
    attempt_no = Column(Integer, nullable=False)
    status = Column(String(30), nullable=False)
    response_code = Column(Integer, nullable=True)
    response_reference = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    attempted_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    locked_at = Column(DateTime(timezone=True), nullable=True)
    locked_by = Column(String(100), nullable=True)
