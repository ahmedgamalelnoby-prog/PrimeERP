from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


LeaveType = Literal["annual", "sick", "unpaid", "other"]


class LeaveBalanceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    employee_id: int = Field(gt=0)
    leave_type: Literal["annual", "sick", "other"]
    entitled_days: Decimal = Field(ge=0, max_digits=10, decimal_places=2)


class LeaveBalanceResponse(BaseModel):
    id: int
    company_id: int
    employee_id: int
    leave_type: str
    entitled_days: Decimal
    consumed_days: Decimal
    available_days: Decimal


class LeaveRequestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    employee_id: int = Field(gt=0)
    leave_type: LeaveType
    start_date: date
    end_date: date
    requested_days: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    reason: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("Leave end date cannot precede start date")
        calendar_span = (self.end_date - self.start_date).days + 1
        if self.requested_days > calendar_span:
            raise ValueError("Requested leave days cannot exceed the calendar date range")
        return self


class LeaveDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: Literal["approve", "reject"]
    reason: str | None = Field(default=None, max_length=2000)


class LeaveRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
    employee_id: int
    leave_type: str
    start_date: date
    end_date: date
    requested_days: Decimal
    reason: str | None
    status: str
    submitted_by_user_id: int
    decided_by_user_id: int | None
    decision_reason: str | None
    decided_at: datetime | None


class AttendanceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    employee_id: int = Field(gt=0)
    attendance_date: date
    check_in_time: datetime
    check_out_time: datetime | None = None

    @model_validator(mode="after")
    def validate_time_order(self):
        if self.check_out_time is not None and self.check_out_time == self.check_in_time:
            raise ValueError("Check-out must differ from check-in")
        return self


class AttendanceCheckOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    check_out_time: datetime


class AttendanceCorrectionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    check_in_time: datetime
    check_out_time: datetime | None = None
    reason: str = Field(min_length=1, max_length=2000)

    @model_validator(mode="after")
    def validate_time_order(self):
        if self.check_out_time is not None and self.check_out_time == self.check_in_time:
            raise ValueError("Corrected check-out must differ from check-in")
        return self


class AttendanceCorrectionDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: Literal["approve", "reject"]
    reason: str | None = Field(default=None, max_length=2000)


class AttendanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
    employee_id: int
    attendance_date: date
    source: str
    check_in_at: datetime
    check_out_at: datetime | None
    recorded_by_user_id: int


class AttendanceCorrectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
    attendance_record_id: int
    proposed_check_in_at: datetime
    proposed_check_out_at: datetime | None
    reason: str
    status: str
    submitted_by_user_id: int
    decided_by_user_id: int | None
    decision_reason: str | None
    decided_at: datetime | None


class OvertimeRequestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    attendance_record_id: int = Field(gt=0)
    requested_hours: Decimal = Field(gt=0, max_digits=8, decimal_places=2)
    reason: str = Field(min_length=1, max_length=2000)


class OvertimeRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
    attendance_record_id: int
    requested_hours: Decimal
    reason: str
    status: str
    submitted_by_user_id: int
    decided_by_user_id: int | None
    decision_reason: str | None
    decided_at: datetime | None
