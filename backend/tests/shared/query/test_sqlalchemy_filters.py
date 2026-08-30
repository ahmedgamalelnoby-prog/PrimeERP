from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy import Boolean, Integer, String, create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
)

from app.shared.query import (
    QueryValidationException,
    SQLAlchemyFilterAdapter,
)


class Base(DeclarativeBase):
    pass


class DemoCompany(Base):
    __tablename__ = "demo_companies"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )


@pytest.fixture()
def db_session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
    )

    Base.metadata.create_all(engine)

    with Session(engine) as session:
        session.add_all(
            [
                DemoCompany(
                    name="PrimeERP",
                    code="PRIME",
                    is_active=True,
                ),
                DemoCompany(
                    name="Prime Hotels",
                    code="HOTEL",
                    is_active=True,
                ),
                DemoCompany(
                    name="Legacy Company",
                    code="OLD",
                    is_active=False,
                ),
            ]
        )

        session.commit()

        yield session


def execute_filter(
    session: Session,
    filters: dict[str, Any],
) -> list[DemoCompany]:
    adapter = SQLAlchemyFilterAdapter()

    query = session.query(DemoCompany)

    query = adapter.apply(
        query=query,
        model=DemoCompany,
        filters=filters,
    )

    return query.order_by(DemoCompany.id).all()


def test_apply_eq_filter(
    db_session: Session,
) -> None:
    result = execute_filter(
        db_session,
        {
            "code": "PRIME",
        },
    )

    assert len(result) == 1
    assert result[0].name == "PrimeERP"


def test_apply_boolean_filter(
    db_session: Session,
) -> None:
    result = execute_filter(
        db_session,
        {
            "is_active": False,
        },
    )

    assert len(result) == 1
    assert result[0].code == "OLD"


def test_apply_contains_filter(
    db_session: Session,
) -> None:
    result = execute_filter(
        db_session,
        {
            "name__contains": "Prime",
        },
    )

    assert len(result) == 2


def test_apply_startswith_filter(
    db_session: Session,
) -> None:
    result = execute_filter(
        db_session,
        {
            "name__startswith": "Legacy",
        },
    )

    assert len(result) == 1
    assert result[0].code == "OLD"


def test_apply_in_filter(
    db_session: Session,
) -> None:
    result = execute_filter(
        db_session,
        {
            "id__in": [1, 3],
        },
    )

    assert [item.id for item in result] == [1, 3]


def test_apply_between_filter(
    db_session: Session,
) -> None:
    result = execute_filter(
        db_session,
        {
            "id__between": [2, 3],
        },
    )

    assert [item.id for item in result] == [2, 3]


def test_apply_multiple_filters(
    db_session: Session,
) -> None:
    result = execute_filter(
        db_session,
        {
            "name__contains": "Prime",
            "is_active": True,
        },
    )

    assert len(result) == 2


def test_reject_unknown_model_field(
    db_session: Session,
) -> None:
    with pytest.raises(QueryValidationException):
        execute_filter(
            db_session,
            {
                "unknown_field": "value",
            },
        )


def test_reject_string_for_in_operator(
    db_session: Session,
) -> None:
    with pytest.raises(QueryValidationException):
        execute_filter(
            db_session,
            {
                "id__in": "1,2,3",
            },
        )


def test_reject_invalid_between_length(
    db_session: Session,
) -> None:
    with pytest.raises(QueryValidationException):
        execute_filter(
            db_session,
            {
                "id__between": [1],
            },
        )


def test_reject_non_boolean_isnull_value(
    db_session: Session,
) -> None:
    with pytest.raises(QueryValidationException):
        execute_filter(
            db_session,
            {
                "name__isnull": "true",
            },
        )