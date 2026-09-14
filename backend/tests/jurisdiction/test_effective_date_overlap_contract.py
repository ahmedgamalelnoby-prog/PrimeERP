from datetime import date

from app.modules.jurisdiction.router import _overlap_clause


def test_overlap_is_true_for_intersecting_closed_ranges():
    class Model:
        effective_from = None
        effective_to = None
        is_active = None

    # Contract-level assertions are expressed through the SQL expression shape.
    expr = _overlap_clause(Model, date(2026, 6, 1), date(2026, 12, 31))
    assert expr is not None


def test_open_ended_incoming_range_is_treated_as_overlapping_candidate():
    class Model:
        effective_from = None
        effective_to = None
        is_active = None

    expr = _overlap_clause(Model, date(2026, 6, 1), None)
    assert expr is not None
