from datetime import datetime, timezone

import pytest

from app.modules.reports.models import ReportDelivery, ReportDefinition
from app.modules.reports.worker import ReportProviderError, calculate_next_run, render_payload


def test_every_schedule_is_future():
    now = datetime(2026, 9, 15, 10, 0, tzinfo=timezone.utc)
    assert calculate_next_run("every:15m", now) == datetime(2026, 9, 15, 10, 15, tzinfo=timezone.utc)


def test_daily_schedule_rolls_to_next_day():
    now = datetime(2026, 9, 15, 10, 0, tzinfo=timezone.utc)
    assert calculate_next_run("daily:09:00", now) == datetime(2026, 9, 16, 9, 0, tzinfo=timezone.utc)


def test_weekly_schedule():
    now = datetime(2026, 9, 15, 10, 0, tzinfo=timezone.utc)  # Tuesday
    assert calculate_next_run("weekly:MON@09:00", now) == datetime(2026, 9, 21, 9, 0, tzinfo=timezone.utc)


def test_monthly_schedule_uses_next_month_when_day_has_passed():
    now = datetime(2026, 9, 20, 10, 0, tzinfo=timezone.utc)
    assert calculate_next_run("monthly:15@09:00", now) == datetime(2026, 10, 15, 9, 0, tzinfo=timezone.utc)


def test_quarterly_schedule_targets_next_quarter_when_current_quarter_date_has_passed():
    now = datetime(2026, 9, 18, 10, 0, tzinfo=timezone.utc)
    assert calculate_next_run("quarterly:1@09:00", now) == datetime(2026, 10, 1, 9, 0, tzinfo=timezone.utc)


def test_quarterly_schedule_targets_current_quarter_when_due_date_is_still_ahead():
    now = datetime(2026, 7, 18, 10, 0, tzinfo=timezone.utc)
    assert calculate_next_run("quarterly:28@11:00", now) == datetime(2026, 7, 28, 11, 0, tzinfo=timezone.utc)


def test_invalid_schedule_rejected():
    with pytest.raises(ValueError):
        calculate_next_run("cron:* * * * *")


def test_unknown_report_provider_never_generates_fake_report():
    definition = ReportDefinition(code="sales", name="Sales", report_type="sales")
    delivery = ReportDelivery(company_id=1, format="json", filters_json="{}")
    with pytest.raises(ReportProviderError):
        render_payload(definition, delivery)


def test_manifest_provider_is_deterministic_and_tenant_scoped():
    definition = ReportDefinition(code="health", name="Health", report_type="manifest", parameters_json='{"period":"monthly"}')
    delivery = ReportDelivery(company_id=7, format="json", filters_json='{"branch_id":2}')
    payload = render_payload(definition, delivery)
    assert '"company_id": 7' in payload
    assert '"branch_id": 2' in payload
