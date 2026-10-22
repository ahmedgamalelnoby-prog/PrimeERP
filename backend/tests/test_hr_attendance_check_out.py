from datetime import datetime
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

from app.modules.hr import service as hr_service_module


class ScalarDb:
    def __init__(self, value):
        self.value = value

    def scalar(self, query):
        return self.value

    def flush(self):
        pass


def _record(check_out_at=None):
    return SimpleNamespace(
        id=41,
        company_id=3,
        employee_id=12,
        attendance_date=datetime(2026, 10, 22).date(),
        check_in_at=datetime(2026, 10, 22, 9, 0, tzinfo=ZoneInfo("Africa/Cairo")),
        check_out_at=check_out_at,
    )


def test_check_out_attendance_sets_company_local_timestamp(monkeypatch):
    record = _record()
    monkeypatch.setattr(hr_service_module, "get_company_setting", lambda db, company_id, key: "Africa/Cairo")
    monkeypatch.setattr(hr_service_module.hr_leave_service, "_assert_overtime_fits", lambda *args, **kwargs: None)

    result = hr_service_module.hr_leave_service.check_out_attendance(
        ScalarDb(record),
        company_id=3,
        record_id=41,
        check_out_time=datetime(2026, 10, 22, 17, 30),
    )

    assert result is record
    assert record.check_out_at == datetime(2026, 10, 22, 17, 30, tzinfo=ZoneInfo("Africa/Cairo"))


def test_check_out_attendance_rejects_duplicate_check_out(monkeypatch):
    record = _record(datetime(2026, 10, 22, 17, 0, tzinfo=ZoneInfo("Africa/Cairo")))
    monkeypatch.setattr(hr_service_module, "get_company_setting", lambda db, company_id, key: "Africa/Cairo")

    with pytest.raises(ValueError, match="already has a check-out"):
        hr_service_module.hr_leave_service.check_out_attendance(
            ScalarDb(record),
            company_id=3,
            record_id=41,
            check_out_time=datetime(2026, 10, 22, 18, 0),
        )


def test_check_out_attendance_rejects_time_before_check_in(monkeypatch):
    record = _record()
    monkeypatch.setattr(hr_service_module, "get_company_setting", lambda db, company_id, key: "Africa/Cairo")

    with pytest.raises(ValueError, match="later than check-in"):
        hr_service_module.hr_leave_service.check_out_attendance(
            ScalarDb(record),
            company_id=3,
            record_id=41,
            check_out_time=datetime(2026, 10, 22, 8, 30),
        )


def test_check_out_attendance_does_not_disclose_cross_company_record():
    with pytest.raises(LookupError, match="Attendance record not found"):
        hr_service_module.hr_leave_service.check_out_attendance(
            ScalarDb(None),
            company_id=999,
            record_id=41,
            check_out_time=datetime(2026, 10, 22, 17, 0),
        )
