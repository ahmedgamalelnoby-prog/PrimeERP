from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.modules.accounting.journals.api.journal_entries import router
from app.modules.accounting.journals.schemas.journal_entry import JournalEntryCreate


def test_journal_entry_api_router_is_registered():
    paths = {route.path for route in router.routes}
    assert "/accounting/journal-entries" in paths
    assert "/accounting/journal-entries/{entry_id}/post" in paths


def test_journal_entry_create_requires_two_lines():
    with pytest.raises(ValidationError):
        JournalEntryCreate(
            company_id=1,
            branch_id=1,
            journal_id=1,
            fiscal_year_id=1,
            period_id=1,
            entry_number="JE-1",
            entry_date="2026-09-11",
            description="Test",
            lines=[
                {
                    "account_combination_id": 1,
                    "debit": Decimal("100"),
                }
            ],
        )


def test_journal_entry_create_accepts_balanced_shape():
    payload = JournalEntryCreate(
        company_id=1,
        branch_id=1,
        journal_id=1,
        fiscal_year_id=1,
        period_id=1,
        entry_number="JE-1",
        entry_date="2026-09-11",
        description="Test",
        lines=[
            {"account_combination_id": 1, "debit": Decimal("100")},
            {"account_combination_id": 2, "credit": Decimal("100")},
        ],
    )
    assert len(payload.lines) == 2
    assert payload.exchange_rate == Decimal("1")
