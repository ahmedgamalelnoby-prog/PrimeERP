from sqlalchemy import CheckConstraint, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from app.database.base import Base


class HRLeaveBalance(Base):
    __tablename__ = "hr_leave_balances"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    leave_type = Column(String(20), nullable=False)
    entitled_days = Column(Numeric(10, 2), nullable=False, default=0)
    consumed_days = Column(Numeric(10, 2), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("company_id", "employee_id", "leave_type", name="uq_hr_leave_balance_employee_type"),
        CheckConstraint("leave_type IN ('annual','sick','other')", name="ck_hr_leave_balance_type"),
        CheckConstraint("entitled_days >= 0 AND consumed_days >= 0", name="ck_hr_leave_balance_values"),
    )


class HRLeaveRequest(Base):
    __tablename__ = "hr_leave_requests"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False, index=True)
    leave_type = Column(String(20), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    requested_days = Column(Numeric(10, 2), nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    submitted_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    decided_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    decision_reason = Column(Text, nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("leave_type IN ('annual','sick','unpaid','other')", name="ck_hr_leave_request_type"),
        CheckConstraint("status IN ('pending','approved','rejected','cancelled')", name="ck_hr_leave_request_status"),
        CheckConstraint("end_date >= start_date", name="ck_hr_leave_request_dates"),
        CheckConstraint("requested_days > 0", name="ck_hr_leave_request_days"),
        Index("ix_hr_leave_request_overlap", "company_id", "employee_id", "start_date", "end_date", "status"),
    )
