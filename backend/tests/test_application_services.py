from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.services.application_services import (
    ApplicationServiceError,
    add_task_dependency,
    assign_helpdesk_ticket,
    transition_helpdesk_ticket,
)


def test_helpdesk_assignment_requires_active_team_member():
    db = MagicMock()
    ticket = SimpleNamespace(id=1, company_id=10, team_id=20)
    db.scalar.side_effect = [ticket, None]

    with pytest.raises(ApplicationServiceError, match="active member"):
        assign_helpdesk_ticket(db, ticket_id=1, company_id=10, member_ref="user-7")


def test_helpdesk_transition_rejects_stage_from_another_team():
    db = MagicMock()
    ticket = SimpleNamespace(id=1, company_id=10, team_id=20)
    foreign_stage = SimpleNamespace(id=8, team_id=99, is_closed=False)
    db.scalar.side_effect = [ticket, foreign_stage]

    with pytest.raises(ApplicationServiceError, match="same company/team"):
        transition_helpdesk_ticket(db, ticket_id=1, company_id=10, stage_id=8)


def test_task_dependency_rejects_self_dependency():
    with pytest.raises(ApplicationServiceError, match="cannot depend on itself"):
        add_task_dependency(MagicMock(), predecessor_id=4, successor_id=4, project_id=2)
