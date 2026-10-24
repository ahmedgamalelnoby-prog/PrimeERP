from datetime import date, datetime
from types import SimpleNamespace

import pytest

from app.modules.company_settings.consumers import hr as hr_policy
from app.modules.hr import service as hr_service_module


@pytest.mark.parametrize("configured_source", ["biometric", "mobile", "integration"])
def test_manual_attendance_route_rejects_non_manual_company_source(monkeypatch, configured_source):
    # Exercise the actual HR service guard, not only the standalone policy helper.
    monkeypatch.setattr(
        hr_policy,
        "policy",
        lambda db, company_id, key: configured_source,
    )
    monkeypatch.setattr(
        hr_service_module,
        "get_company_setting",
        lambda db, company_id, key: configured_source,
    )

    payload = SimpleNamespace(
        employee_id=12,
        attendance_date=date(2026, 10, 22),
        check_in_time=datetime(2026, 10, 22, 9, 0),
        check_out_time=None,
    )

    with pytest.raises(ValueError, match="Manual attendance entry is disabled"):
        hr_service_module.hr_leave_service.create_attendance(
            object(),
            company_id=3,
            payload=payload,
            actor_user_id=7,
        )
