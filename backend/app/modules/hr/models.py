from sqlalchemy import CheckConstraint, Column, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
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


class HRAttendanceRecord(Base):
    __tablename__ = "hr_attendance_records"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    attendance_date = Column(Date, nullable=False)
    source = Column(String(20), nullable=False, default="manual")
    check_in_at = Column(DateTime(timezone=True), nullable=False)
    check_out_at = Column(DateTime(timezone=True), nullable=True)
    recorded_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("company_id", "employee_id", "attendance_date", name="uq_hr_attendance_employee_date"),
        CheckConstraint("source IN ('manual','biometric','mobile','integration')", name="ck_hr_attendance_source"),
        CheckConstraint("check_out_at IS NULL OR check_out_at > check_in_at", name="ck_hr_attendance_time_order"),
        Index("ix_hr_attendance_company_date", "company_id", "attendance_date"),
    )


class HRAttendanceCorrection(Base):
    __tablename__ = "hr_attendance_corrections"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    attendance_record_id = Column(Integer, ForeignKey("hr_attendance_records.id", ondelete="CASCADE"), nullable=False, index=True)
    proposed_check_in_at = Column(DateTime(timezone=True), nullable=False)
    proposed_check_out_at = Column(DateTime(timezone=True), nullable=True)
    reason = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    submitted_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    decided_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    decision_reason = Column(Text, nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("status IN ('pending','approved','rejected')", name="ck_hr_attendance_correction_status"),
        CheckConstraint("proposed_check_out_at IS NULL OR proposed_check_out_at > proposed_check_in_at", name="ck_hr_attendance_correction_time_order"),
        Index("ix_hr_attendance_correction_status", "company_id", "status", "created_at"),
    )
