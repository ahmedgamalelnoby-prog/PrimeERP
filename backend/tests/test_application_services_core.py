from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.services.application_services import ApplicationServiceError, add_task_dependency, assign_helpdesk_ticket, complete_task, create_helpdesk_ticket


class _ScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar(self):
        return self.value


class _DB:
    def __init__(self, values):
        self.values = list(values)
        self.added = []

    def scalar(self, _statement):
        return self.values.pop(0) if self.values else None

    def add(self, value):
        self.added.append(value)

    def flush(self):
        return None


def test_create_helpdesk_ticket_rejects_inactive_assignee():
    team = SimpleNamespace(id=1, company_id=10)
    stage = SimpleNamespace(id=2, team_id=1)
    db = _DB([team, stage, None])

    with pytest.raises(ApplicationServiceError, match="active member"):
        create_helpdesk_ticket(db, company_id=10, team_id=1, stage_id=2, ticket_no="HD-1", subject="Test", assignee_ref="u1")


def test_assign_helpdesk_ticket_requires_team_membership():
    ticket = SimpleNamespace(id=5, team_id=2, company_id=10)
    db = _DB([ticket, None])

    with pytest.raises(ApplicationServiceError, match="active member"):
        assign_helpdesk_ticket(db, ticket_id=5, company_id=10, member_ref="u1")


def test_create_helpdesk_ticket_accepts_active_assignee():
    team = SimpleNamespace(id=1, company_id=10)
    stage = SimpleNamespace(id=2, team_id=1)
    member = SimpleNamespace(team_id=1, member_ref="u1", active=True)
    db = _DB([team, stage, member])

    ticket = create_helpdesk_ticket(db, company_id=10, team_id=1, stage_id=2, ticket_no="HD-1", subject="Test", assignee_ref="u1")
    assert ticket.company_id == 10
    assert ticket.assignee_ref == "u1"
    assert db.added == [ticket]


def test_application_service_error_is_value_error():
    assert issubclass(ApplicationServiceError, ValueError)
