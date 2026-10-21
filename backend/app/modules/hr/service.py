from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.company_settings.service import get_company_setting
from app.modules.enterprise.models import Employee
from app.modules.hr.models import HRLeaveBalance, HRLeaveRequest, HRAttendanceRecord, HRAttendanceCorrection


PAID_LEAVE_TYPES = {"annual", "sick", "other"}


class HRLeaveService:
    @staticmethod
    def _employee(db: Session, *, company_id: int, employee_id: int, lock: bool = False) -> Employee:
        query = select(Employee).where(
            Employee.id == employee_id,
            Employee.company_id == company_id,
            Employee.is_active.is_(True),
        )
        if lock:
            query = query.with_for_update()
        employee = db.scalar(query)
        if employee is None:
            raise LookupError("Active employee not found for this company")
        return employee

    @staticmethod
    def list_balances(db: Session, *, company_id: int) -> list[HRLeaveBalance]:
        return list(db.scalars(
            select(HRLeaveBalance)
            .where(HRLeaveBalance.company_id == company_id)
            .order_by(HRLeaveBalance.employee_id, HRLeaveBalance.leave_type)
        ).all())

    def update_balance(self, db: Session, *, company_id: int, employee_id: int, leave_type: str, entitled_days: Decimal) -> HRLeaveBalance:
        self._employee(db, company_id=company_id, employee_id=employee_id, lock=True)
        balance = db.scalar(select(HRLeaveBalance).where(
            HRLeaveBalance.company_id == company_id,
            HRLeaveBalance.employee_id == employee_id,
            HRLeaveBalance.leave_type == leave_type,
        ).with_for_update())
        if balance is None:
            balance = HRLeaveBalance(
                company_id=company_id,
                employee_id=employee_id,
                leave_type=leave_type,
                entitled_days=entitled_days,
                consumed_days=Decimal("0"),
            )
            db.add(balance)
        else:
            consumed = Decimal(balance.consumed_days or 0)
            if get_company_setting(db, company_id, "hr.allow_negative_leave_balance") is not True and entitled_days < consumed:
                raise ValueError("Entitled leave days cannot be set below already consumed days while negative balances are disabled")
            balance.entitled_days = entitled_days
        db.flush()
        return balance

    @staticmethod
    def _consume_balance(db: Session, *, company_id: int, employee_id: int, leave_type: str, days: Decimal) -> None:
        if leave_type == "unpaid":
            return
        balance = db.scalar(select(HRLeaveBalance).where(
            HRLeaveBalance.company_id == company_id,
            HRLeaveBalance.employee_id == employee_id,
            HRLeaveBalance.leave_type == leave_type,
        ).with_for_update())
        allow_negative = get_company_setting(db, company_id, "hr.allow_negative_leave_balance") is True
        if balance is None:
            if not allow_negative:
                raise ValueError("No leave balance is configured for this employee and leave type")
            balance = HRLeaveBalance(
                company_id=company_id,
                employee_id=employee_id,
                leave_type=leave_type,
                entitled_days=Decimal("0"),
                consumed_days=Decimal("0"),
            )
            db.add(balance)
            db.flush()
        available = Decimal(balance.entitled_days or 0) - Decimal(balance.consumed_days or 0)
        if not allow_negative and days > available:
            raise ValueError("Requested leave exceeds the employee's available balance")
        balance.consumed_days = Decimal(balance.consumed_days or 0) + days

    def create_request(self, db: Session, *, company_id: int, payload, submitted_by_user_id: int) -> HRLeaveRequest:
        employee = self._employee(db, company_id=company_id, employee_id=payload.employee_id, lock=True)
        overlap = db.scalar(select(HRLeaveRequest.id).where(
            HRLeaveRequest.company_id == company_id,
            HRLeaveRequest.employee_id == employee.id,
            HRLeaveRequest.status.in_({"pending", "approved"}),
            HRLeaveRequest.start_date <= payload.end_date,
            HRLeaveRequest.end_date >= payload.start_date,
        ).limit(1))
        if overlap is not None:
            raise ValueError("This employee already has a pending or approved leave request for an overlapping date range")
        requires_approval = get_company_setting(db, company_id, "hr.leave_requires_approval") is True
        request = HRLeaveRequest(
            company_id=company_id,
            employee_id=employee.id,
            leave_type=payload.leave_type,
            start_date=payload.start_date,
            end_date=payload.end_date,
            requested_days=payload.requested_days,
            reason=payload.reason,
            status="pending" if requires_approval else "approved",
            submitted_by_user_id=submitted_by_user_id,
        )
        db.add(request)
        db.flush()
        if not requires_approval:
            self._consume_balance(
                db,
                company_id=company_id,
                employee_id=employee.id,
                leave_type=payload.leave_type,
                days=Decimal(payload.requested_days),
            )
            request.decided_by_user_id = submitted_by_user_id
            request.decided_at = datetime.now(timezone.utc)
            request.decision_reason = "Automatically approved by company policy"
        db.flush()
        return request

    def decide_request(self, db: Session, *, company_id: int, request_id: int, actor_user_id: int, decision: str, reason: str | None) -> HRLeaveRequest:
        request = db.scalar(select(HRLeaveRequest).where(
            HRLeaveRequest.id == request_id,
            HRLeaveRequest.company_id == company_id,
        ).with_for_update())
        if request is None:
            raise LookupError("Leave request not found")
        if request.status != "pending":
            raise ValueError("Only pending leave requests can be decided")
        if request.submitted_by_user_id == actor_user_id and get_company_setting(db, company_id, "workflow.allow_self_approval") is not True:
            raise ValueError("The requester cannot approve or reject their own leave request under company policy")
        if decision == "approve":
            self._employee(db, company_id=company_id, employee_id=request.employee_id, lock=True)
            self._consume_balance(
                db,
                company_id=company_id,
                employee_id=request.employee_id,
                leave_type=request.leave_type,
                days=Decimal(request.requested_days),
            )
            request.status = "approved"
        else:
            request.status = "rejected"
        request.decided_by_user_id = actor_user_id
        request.decided_at = datetime.now(timezone.utc)
        request.decision_reason = reason
        db.flush()
        return request

    def cancel_request(self, db: Session, *, company_id: int, request_id: int, actor_user_id: int) -> HRLeaveRequest:
        request = db.scalar(select(HRLeaveRequest).where(
            HRLeaveRequest.id == request_id,
            HRLeaveRequest.company_id == company_id,
        ).with_for_update())
        if request is None:
            raise LookupError("Leave request not found")
        if request.submitted_by_user_id != actor_user_id:
            raise ValueError("Only the requester can cancel this leave request")
        if request.status not in {"pending", "approved"}:
            raise ValueError("Only pending or approved leave requests can be cancelled")
        company_timezone = get_company_setting(db, company_id, "general.timezone")
        company_today = datetime.now(ZoneInfo(company_timezone)).date()
        if request.status == "approved" and request.start_date <= company_today:
            raise ValueError("An approved leave cannot be cancelled after its start date in the company timezone")
        if request.status == "approved" and request.leave_type in PAID_LEAVE_TYPES:
            balance = db.scalar(select(HRLeaveBalance).where(
                HRLeaveBalance.company_id == company_id,
                HRLeaveBalance.employee_id == request.employee_id,
                HRLeaveBalance.leave_type == request.leave_type,
            ).with_for_update())
            if balance is None or Decimal(balance.consumed_days or 0) < Decimal(request.requested_days):
                raise ValueError("The consumed leave balance could not be restored safely")
            balance.consumed_days = Decimal(balance.consumed_days or 0) - Decimal(request.requested_days)
        request.status = "cancelled"
        request.decided_by_user_id = actor_user_id
        request.decided_at = datetime.now(timezone.utc)
        request.decision_reason = "Cancelled by requester"
        db.flush()
        return request


    @staticmethod
    def _local_datetime(value: datetime, timezone_name: str) -> datetime:
        zone = ZoneInfo(timezone_name)
        return value.replace(tzinfo=zone) if value.tzinfo is None else value.astimezone(zone)

    def list_attendance(self, db: Session, *, company_id: int, attendance_date=None) -> list[HRAttendanceRecord]:
        query = select(HRAttendanceRecord).where(HRAttendanceRecord.company_id == company_id)
        if attendance_date is not None:
            query = query.where(HRAttendanceRecord.attendance_date == attendance_date)
        return list(db.scalars(query.order_by(HRAttendanceRecord.attendance_date.desc(), HRAttendanceRecord.employee_id)).all())

    def create_attendance(self, db: Session, *, company_id: int, payload, actor_user_id: int) -> HRAttendanceRecord:
        source = get_company_setting(db, company_id, "hr.attendance_source")
        if source != "manual":
            raise ValueError(f"Manual attendance entry is disabled because the configured source is '{source}'; its connector is not available")
        self._employee(db, company_id=company_id, employee_id=payload.employee_id, lock=True)
        timezone_name = get_company_setting(db, company_id, "general.timezone")
        check_in = self._local_datetime(payload.check_in_time, timezone_name)
        if check_in.date() != payload.attendance_date:
            raise ValueError("Check-in timestamp must fall on the selected attendance date in the company timezone")
        check_out = self._local_datetime(payload.check_out_time, timezone_name) if payload.check_out_time else None
        if check_out is not None and check_out <= check_in:
            raise ValueError("Check-out must be later than check-in")
        existing = db.scalar(select(HRAttendanceRecord.id).where(
            HRAttendanceRecord.company_id == company_id,
            HRAttendanceRecord.employee_id == payload.employee_id,
            HRAttendanceRecord.attendance_date == payload.attendance_date,
        ).limit(1))
        if existing is not None:
            raise ValueError("Attendance is already recorded for this employee and date")
        record = HRAttendanceRecord(
            company_id=company_id,
            employee_id=payload.employee_id,
            attendance_date=payload.attendance_date,
            source="manual",
            check_in_at=check_in,
            check_out_at=check_out,
            recorded_by_user_id=actor_user_id,
        )
        db.add(record)
        db.flush()
        return record

    def list_corrections(self, db: Session, *, company_id: int) -> list[HRAttendanceCorrection]:
        return list(db.scalars(
            select(HRAttendanceCorrection)
            .where(HRAttendanceCorrection.company_id == company_id)
            .order_by(HRAttendanceCorrection.created_at.desc(), HRAttendanceCorrection.id.desc())
        ).all())

    def create_correction(self, db: Session, *, company_id: int, record_id: int, payload, actor_user_id: int) -> HRAttendanceCorrection:
        record = db.scalar(select(HRAttendanceRecord).where(
            HRAttendanceRecord.id == record_id,
            HRAttendanceRecord.company_id == company_id,
        ).with_for_update())
        if record is None:
            raise LookupError("Attendance record not found")
        timezone_name = get_company_setting(db, company_id, "general.timezone")
        check_in = self._local_datetime(payload.check_in_time, timezone_name)
        if check_in.date() != record.attendance_date:
            raise ValueError("Corrected check-in must fall on the attendance date in the company timezone")
        check_out = self._local_datetime(payload.check_out_time, timezone_name) if payload.check_out_time else None
        if check_out is not None and check_out <= check_in:
            raise ValueError("Corrected check-out must be later than check-in")
        pending = db.scalar(select(HRAttendanceCorrection.id).where(
            HRAttendanceCorrection.company_id == company_id,
            HRAttendanceCorrection.attendance_record_id == record.id,
            HRAttendanceCorrection.status == "pending",
        ).limit(1))
        if pending is not None:
            raise ValueError("An attendance correction is already awaiting a decision")
        requires_approval = get_company_setting(db, company_id, "hr.require_attendance_approval") is True
        correction = HRAttendanceCorrection(
            company_id=company_id,
            attendance_record_id=record.id,
            proposed_check_in_at=check_in,
            proposed_check_out_at=check_out,
            reason=payload.reason,
            status="pending" if requires_approval else "approved",
            submitted_by_user_id=actor_user_id,
        )
        db.add(correction)
        db.flush()
        if not requires_approval:
            record.check_in_at = check_in
            record.check_out_at = check_out
            correction.decided_by_user_id = actor_user_id
            correction.decided_at = datetime.now(timezone.utc)
            correction.decision_reason = "Automatically applied by company policy"
        db.flush()
        return correction

    def decide_correction(self, db: Session, *, company_id: int, correction_id: int, actor_user_id: int, decision: str, reason: str | None) -> HRAttendanceCorrection:
        correction = db.scalar(select(HRAttendanceCorrection).where(
            HRAttendanceCorrection.id == correction_id,
            HRAttendanceCorrection.company_id == company_id,
        ).with_for_update())
        if correction is None:
            raise LookupError("Attendance correction not found")
        if correction.status != "pending":
            raise ValueError("Only pending attendance corrections can be decided")
        if correction.submitted_by_user_id == actor_user_id and get_company_setting(db, company_id, "workflow.allow_self_approval") is not True:
            raise ValueError("The requester cannot decide their own attendance correction under company policy")
        record = db.scalar(select(HRAttendanceRecord).where(
            HRAttendanceRecord.id == correction.attendance_record_id,
            HRAttendanceRecord.company_id == company_id,
        ).with_for_update())
        if record is None:
            raise LookupError("Attendance record not found")
        if decision == "approve":
            record.check_in_at = correction.proposed_check_in_at
            record.check_out_at = correction.proposed_check_out_at
            correction.status = "approved"
        else:
            correction.status = "rejected"
        correction.decided_by_user_id = actor_user_id
        correction.decided_at = datetime.now(timezone.utc)
        correction.decision_reason = reason
        db.flush()
        return correction



hr_leave_service = HRLeaveService()
