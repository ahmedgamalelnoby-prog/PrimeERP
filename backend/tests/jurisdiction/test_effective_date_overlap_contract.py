from datetime import date

from sqlalchemy import Boolean, Column, Date

from app.modules.jurisdiction.router import _overlap_clause


class Model:
    effective_from = Column(Date)
    effective_to = Column(Date)
    is_active = Column(Boolean)


def test_overlap_expression_builds_for_closed_range():
    expr = _overlap_clause(Model, date(2026, 6, 1), date(2026, 12, 31))
    assert expr is not None


def test_overlap_expression_builds_for_open_ended_range():
    expr = _overlap_clause(Model, date(2026, 6, 1), None)
    assert expr is not None
