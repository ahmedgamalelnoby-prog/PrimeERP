from typing import Literal
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from decimal import Decimal
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.audit.service import record_audit_event
from app.modules.companies.models import Company
from app.core.context import get_effective_tenant_id
from app.core.permissions import require_permission
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models.user import User
from app.modules.saas.entitlements import require_module
from app.modules.hr.models import HRLeaveBalance, HRLeaveRequest, HRAttendanceRecord, HRAttendanceCorrection, HROvertimeRequest
from app.modules.hr.schemas import AttendanceCheckOut, AttendanceCreate, AttendanceCorrectionCreate, AttendanceCorrectionDecision, AttendanceCorrectionResponse, AttendanceResponse, LeaveBalanceResponse, LeaveBalanceUpdate, LeaveDecision, LeaveRequestCreate, LeaveRequestResponse, OvertimeRequestCreate, OvertimeRequestResponse
from app.modules.hr.service import hr_leave_service
from app.modules.company_settings.consumers.hr import attendance_source_allowed

router = APIRouter(
    prefix="/hr",
    tags=["HR"],
    dependencies=[Depends(require_module("hr"))],
)


def _tenant(user: User) -> int:
    if get_effective_tenant_id(user) is None:
        raise HTTPException(403, "User is not assigned to a tenant")
    return get_effective_tenant_id(user)


def _require_manual_attendance_source(db: Session, company_id: int) -> None:
    """Fail closed when manual attendance writes are not the configured source."""
    try:
        allowed = attendance_source_allowed(db, company_id, "manual")
    except Exception:
        raise HTTPException(503, "Attendance source policy could not be verified; manual attendance is denied.") from None
    if not allowed:
        raise HTTPException(409, "Manual attendance changes are disabled by company policy; use the configured attendance source.")


def _company_for_tenant(db: Session, company_id: int, tenant_id: int) -> Company:
    company = db.scalar(
        select(Company).where(
            Company.id == company_id,
            Company.tenant_id == tenant_id,
            Company.is_active.is_(True),
        )
    )
    if company is None:
        # Do not disclose whether a company exists in another tenant.
        raise HTTPException(404, "Company not found")
    return company


class WorkforceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str | None = Field(default=None, min_length=1, max_length=150)
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=1000)
    preferred_language: Literal["ar", "en"] = "ar"


@router.get(
    "/workforce",
    dependencies=[Depends(require_permission("enterprise.access"))],
)
def workforce(
    company_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tenant_id = _tenant(current_user)
    _company_for_tenant(db, company_id, tenant_id)

    users = list(
        db.scalars(
            select(User)
            .where(
                User.tenant_id == tenant_id,
                User.is_deleted.is_(False),
            )
            .order_by(User.full_name, User.id)
        ).all()
    )
    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "phone": user.phone,
            "address": user.address,
            "is_active": user.is_active,
            "role_id": user.role_id,
        }
        for user in users
    ]


@router.patch(
    "/workforce/{user_id}",
    dependencies=[Depends(require_permission("enterprise.write"))],
)
def update_workforce(
    user_id: int,
    payload: WorkforceUpdate,
    company_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tenant_id = _tenant(current_user)
    _company_for_tenant(db, company_id, tenant_id)

    obj = db.scalar(
        select(User).where(
            User.id == user_id,
            User.tenant_id == tenant_id,
            User.is_deleted.is_(False),
        )
    )
    if obj is None:
        raise HTTPException(404, "Employee/user not found")

    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(422, "At least one workforce field must be supplied")

    for key, value in changes.items():
        setattr(obj, key, value)

    record_audit_event(
        db,
        action="hr.workforce_profile_updated",
        entity_type="user",
        entity_id=obj.id,
        user_id=current_user.id,
        tenant_id=tenant_id,
        company_id=company_id,
        metadata={"changed_fields": sorted(changes)},
    )
    db.commit()
    db.refresh(obj)
    return {
        "id": obj.id,
        "full_name": obj.full_name,
        "phone": obj.phone,
        "address": obj.address,
        "preferred_language": obj.preferred_language,
    }


def _leave_audit(db: Session, *, action: str, request_id: int, user: User, tenant_id: int, company_id: int, leave_type: str, status: str, days: Decimal) -> None:
    record_audit_event(
        db,
        action=action,
        entity_type="hr_leave_request",
        entity_id=request_id,
        user_id=user.id,
        tenant_id=tenant_id,
        company_id=company_id,
        metadata={"leave_type": leave_type, "status": status, "requested_days": str(days)},
    )


@router.put(
    "/leave-balances",
    response_model=LeaveBalanceResponse,
    dependencies=[Depends(require_permission("enterprise.write"))],
)
def update_leave_balance(
    payload: LeaveBalanceUpdate,
    company_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tenant_id = _tenant(current_user)
    _company_for_tenant(db, company_id, tenant_id)
    try:
        balance = hr_leave_service.update_balance(
            db,
            company_id=company_id,
            employee_id=payload.employee_id,
            leave_type=payload.leave_type,
            entitled_days=payload.entitled_days,
        )
        db.commit()
        db.refresh(balance)
        return LeaveBalanceResponse(
            id=balance.id,
            company_id=balance.company_id,
            employee_id=balance.employee_id,
            leave_type=balance.leave_type,
            entitled_days=balance.entitled_days,
            consumed_days=balance.consumed_days,
            available_days=Decimal(balance.entitled_days) - Decimal(balance.consumed_days),
        )
    except LookupError as exc:
        db.rollback()
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(409, str(exc)) from exc


@router.get(
    "/leave-balances",
    response_model=list[LeaveBalanceResponse],
    dependencies=[Depends(require_permission("enterprise.access"))],
)
def list_leave_balances(
    company_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tenant_id = _tenant(current_user)
    _company_for_tenant(db, company_id, tenant_id)
    balances = hr_leave_service.list_balances(db, company_id=company_id)
    return [
        LeaveBalanceResponse(
            id=row.id,
            company_id=row.company_id,
            employee_id=row.employee_id,
            leave_type=row.leave_type,
            entitled_days=row.entitled_days,
            consumed_days=row.consumed_days,
            available_days=Decimal(row.entitled_days) - Decimal(row.consumed_days),
        )
        for row in balances
    ]


@router.post(
    "/leave-requests",
    response_model=LeaveRequestResponse,
    status_code=201,
    dependencies=[Depends(require_permission("enterprise.write"))],
)
def create_leave_request(
    payload: LeaveRequestCreate,
    company_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tenant_id = _tenant(current_user)
    _company_for_tenant(db, company_id, tenant_id)
    try:
        request = hr_leave_service.create_request(
            db,
            company_id=company_id,
            payload=payload,
            submitted_by_user_id=current_user.id,
        )
        _leave_audit(
            db,
            action="hr.leave_request_submitted",
            request_id=request.id,
            user=current_user,
            tenant_id=tenant_id,
            company_id=company_id,
            leave_type=request.leave_type,
            status=request.status,
            days=Decimal(request.requested_days),
        )
        db.commit()
        db.refresh(request)
        return request
    except LookupError as exc:
        db.rollback()
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(409, str(exc)) from exc


@router.get(
    "/leave-requests",
    response_model=list[LeaveRequestResponse],
    dependencies=[Depends(require_permission("enterprise.access"))],
)
def list_leave_requests(
    company_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tenant_id = _tenant(current_user)
    _company_for_tenant(db, company_id, tenant_id)
    return list(db.scalars(
        select(HRLeaveRequest)
        .where(HRLeaveRequest.company_id == company_id)
        .order_by(HRLeaveRequest.created_at.desc(), HRLeaveRequest.id.desc())
    ).all())


@router.post(
    "/leave-requests/{request_id}/decision",
    response_model=LeaveRequestResponse,
    dependencies=[Depends(require_permission("enterprise.post"))],
)
def decide_leave_request(
    request_id: int,
    payload: LeaveDecision,
    company_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tenant_id = _tenant(current_user)
    _company_for_tenant(db, company_id, tenant_id)
    try:
        request = hr_leave_service.decide_request(
            db,
            company_id=company_id,
            request_id=request_id,
            actor_user_id=current_user.id,
            decision=payload.decision,
            reason=payload.reason,
        )
        _leave_audit(
            db,
            action="hr.leave_request_approved" if payload.decision == "approve" else "hr.leave_request_rejected",
            request_id=request.id,
            user=current_user,
            tenant_id=tenant_id,
            company_id=company_id,
            leave_type=request.leave_type,
            status=request.status,
            days=Decimal(request.requested_days),
        )
        db.commit()
        db.refresh(request)
        return request
    except LookupError as exc:
        db.rollback()
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(409, str(exc)) from exc


@router.post(
    "/leave-requests/{request_id}/cancel",
    response_model=LeaveRequestResponse,
    dependencies=[Depends(require_permission("enterprise.write"))],
)
def cancel_leave_request(
    request_id: int,
    company_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tenant_id = _tenant(current_user)
    _company_for_tenant(db, company_id, tenant_id)
    try:
        request = hr_leave_service.cancel_request(
            db,
            company_id=company_id,
            request_id=request_id,
            actor_user_id=current_user.id,
        )
        _leave_audit(
            db,
            action="hr.leave_request_cancelled",
            request_id=request.id,
            user=current_user,
            tenant_id=tenant_id,
            company_id=company_id,
            leave_type=request.leave_type,
            status=request.status,
            days=Decimal(request.requested_days),
        )
        db.commit()
        db.refresh(request)
        return request
    except LookupError as exc:
        db.rollback()
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(409, str(exc)) from exc


def _attendance_audit(db: Session, *, action: str, entity_id: int, user: User, tenant_id: int, company_id: int, status: str) -> None:
    record_audit_event(
        db,
        action=action,
        entity_type="hr_attendance_correction" if "correction" in action else "hr_attendance",
        entity_id=entity_id,
        user_id=user.id,
        tenant_id=tenant_id,
        company_id=company_id,
        metadata={"status": status},
    )


def _overtime_audit(db: Session, *, action: str, request_id: int, user: User, tenant_id: int, company_id: int, status: str, hours: Decimal) -> None:
    record_audit_event(
        db,
        action=action,
        entity_type="hr_overtime_request",
        entity_id=request_id,
        user_id=user.id,
        tenant_id=tenant_id,
        company_id=company_id,
        metadata={"status": status, "requested_hours": str(hours)},
    )



@router.get(
    "/attendance",
    response_model=list[AttendanceResponse],
    dependencies=[Depends(require_permission("enterprise.access"))],
)
def list_attendance(
    company_id: int = Query(..., gt=0),
    attendance_date: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tenant_id = _tenant(current_user)
    _company_for_tenant(db, company_id, tenant_id)
    return hr_leave_service.list_attendance(db, company_id=company_id, attendance_date=attendance_date)


@router.post(
    "/attendance",
    response_model=AttendanceResponse,
    status_code=201,
    dependencies=[Depends(require_permission("enterprise.write"))],
)
def create_attendance(
    payload: AttendanceCreate,
    company_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tenant_id = _tenant(current_user)
    _company_for_tenant(db, company_id, tenant_id)
    # This endpoint is the manual-entry path. Do not silently accept it
    # when the company has selected another source.
    _require_manual_attendance_source(db, company_id)
    try:
        record = hr_leave_service.create_attendance(
            db, company_id=company_id, payload=payload, actor_user_id=current_user.id
        )
        _attendance_audit(
            db, action="hr.attendance_recorded", entity_id=record.id, user=current_user,
            tenant_id=tenant_id, company_id=company_id, status="recorded",
        )
        db.commit()
        db.refresh(record)
        return record
    except LookupError as exc:
        db.rollback()
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(409, str(exc)) from exc


@router.post(
    "/attendance/{record_id}/check-out",
    response_model=AttendanceResponse,
    dependencies=[Depends(require_permission("enterprise.write"))],
)
def check_out_attendance(
    record_id: int,
    payload: AttendanceCheckOut,
    company_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tenant_id = _tenant(current_user)
    _company_for_tenant(db, company_id, tenant_id)
    # Check-out is also a manual write and follows the same source policy.
    _require_manual_attendance_source(db, company_id)
    try:
        record = hr_leave_service.check_out_attendance(
            db,
            company_id=company_id,
            record_id=record_id,
            check_out_time=payload.check_out_time,
        )
        _attendance_audit(
            db,
            action="hr.attendance_checked_out",
            entity_id=record.id,
            user=current_user,
            tenant_id=tenant_id,
            company_id=company_id,
            status="checked_out",
        )
        db.commit()
        db.refresh(record)
        return record
    except LookupError as exc:
        db.rollback()
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(409, str(exc)) from exc


@router.post(
    "/attendance/{record_id}/corrections",
    response_model=AttendanceCorrectionResponse,
    status_code=201,
    dependencies=[Depends(require_permission("enterprise.write"))],
)
def create_attendance_correction(
    record_id: int,
    payload: AttendanceCorrectionCreate,
    company_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tenant_id = _tenant(current_user)
    _company_for_tenant(db, company_id, tenant_id)
    try:
        correction = hr_leave_service.create_correction(
            db, company_id=company_id, record_id=record_id,
            payload=payload, actor_user_id=current_user.id,
        )
        _attendance_audit(
            db, action="hr.attendance_correction_submitted", entity_id=correction.id,
            user=current_user, tenant_id=tenant_id, company_id=company_id, status=correction.status,
        )
        db.commit()
        db.refresh(correction)
        return correction
    except LookupError as exc:
        db.rollback()
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(409, str(exc)) from exc


@router.get(
    "/attendance-corrections",
    response_model=list[AttendanceCorrectionResponse],
    dependencies=[Depends(require_permission("enterprise.access"))],
)
def list_attendance_corrections(
    company_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tenant_id = _tenant(current_user)
    _company_for_tenant(db, company_id, tenant_id)
    return hr_leave_service.list_corrections(db, company_id=company_id)


@router.post(
    "/attendance-corrections/{correction_id}/decision",
    response_model=AttendanceCorrectionResponse,
    dependencies=[Depends(require_permission("enterprise.post"))],
)
def decide_attendance_correction(
    correction_id: int,
    payload: AttendanceCorrectionDecision,
    company_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tenant_id = _tenant(current_user)
    _company_for_tenant(db, company_id, tenant_id)
    try:
        correction = hr_leave_service.decide_correction(
            db, company_id=company_id, correction_id=correction_id,
            actor_user_id=current_user.id, decision=payload.decision, reason=payload.reason,
        )
        action = "hr.attendance_correction_approved" if payload.decision == "approve" else "hr.attendance_correction_rejected"
        _attendance_audit(
            db, action=action, entity_id=correction.id, user=current_user,
            tenant_id=tenant_id, company_id=company_id, status=correction.status,
        )
        db.commit()
        db.refresh(correction)
        return correction
    except LookupError as exc:
        db.rollback()
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(409, str(exc)) from exc


@router.get(
    "/overtime-requests",
    response_model=list[OvertimeRequestResponse],
    dependencies=[Depends(require_permission("enterprise.access"))],
)
def list_overtime_requests(
    company_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tenant_id = _tenant(current_user)
    _company_for_tenant(db, company_id, tenant_id)
    return hr_leave_service.list_overtime_requests(db, company_id=company_id)


@router.post(
    "/overtime-requests",
    response_model=OvertimeRequestResponse,
    status_code=201,
    dependencies=[Depends(require_permission("enterprise.write"))],
)
def create_overtime_request(
    payload: OvertimeRequestCreate,
    company_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tenant_id = _tenant(current_user)
    _company_for_tenant(db, company_id, tenant_id)
    try:
        request = hr_leave_service.create_overtime_request(
            db, company_id=company_id, payload=payload, actor_user_id=current_user.id
        )
        _overtime_audit(
            db,
            action="hr.overtime_request_submitted",
            request_id=request.id,
            user=current_user,
            tenant_id=tenant_id,
            company_id=company_id,
            status=request.status,
            hours=Decimal(request.requested_hours),
        )
        db.commit()
        db.refresh(request)
        return request
    except LookupError as exc:
        db.rollback()
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(409, str(exc)) from exc


@router.post(
    "/overtime-requests/{request_id}/decision",
    response_model=OvertimeRequestResponse,
    dependencies=[Depends(require_permission("enterprise.post"))],
)
def decide_overtime_request(
    request_id: int,
    payload: LeaveDecision,
    company_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tenant_id = _tenant(current_user)
    _company_for_tenant(db, company_id, tenant_id)
    try:
        request = hr_leave_service.decide_overtime_request(
            db,
            company_id=company_id,
            request_id=request_id,
            actor_user_id=current_user.id,
            decision=payload.decision,
            reason=payload.reason,
        )
        _overtime_audit(
            db,
            action="hr.overtime_request_approved" if payload.decision == "approve" else "hr.overtime_request_rejected",
            request_id=request.id,
            user=current_user,
            tenant_id=tenant_id,
            company_id=company_id,
            status=request.status,
            hours=Decimal(request.requested_hours),
        )
        db.commit()
        db.refresh(request)
        return request
    except LookupError as exc:
        db.rollback()
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(409, str(exc)) from exc
