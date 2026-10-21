from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from decimal import Decimal

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.modules.company_settings.service import get_company_setting
from app.modules.enterprise.models import Employee
from app.modules.hr.models import HRLeaveBalance, HRLeaveRequest


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
        if request.submitted_by_user_id == actor_user_id:
            raise ValueError("The requester cannot approve or reject their own leave request")
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


hr_leave_service = HRLeaveService()
