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
    SQLAlchemySearchAdapter,
)


class Base(DeclarativeBase):
    pass


class DemoCompany(Base):
    __tablename__ = "search_demo_companies"

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

    email: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    @property
    def display_name(self) -> str:
        return f"{self.code} - {self.name}"


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
                    name="Alpha Foods",
                    code="ALPHA",
                    email="info@alpha.com",
                    is_active=True,
                ),
                DemoCompany(
                    name="Prime Restaurants",
                    code="PRIME",
                    email="contact@prime.com",
                    is_active=True,
                ),
                DemoCompany(
                    name="Nile Hospitality",
                    code="NILE",
                    email="hotel@nile.com",
                    is_active=False,
                ),
            ]
        )

        session.commit()

        yield session


def execute_search(
    session: Session,
    search: Any,
    *,
    search_fields: set[str] | None,
) -> list[DemoCompany]:
    adapter = SQLAlchemySearchAdapter()

    query = session.query(DemoCompany)

    query = adapter.apply(
        query=query,
        model=DemoCompany,
        search=search,
        search_fields=search_fields,
    )

    return query.order_by(
        DemoCompany.id.asc()
    ).all()


def test_search_by_name(
    db_session: Session,
) -> None:
    result = execute_search(
        db_session,
        "Prime",
        search_fields={
            "name",
            "code",
            "email",
        },
    )

    assert [item.name for item in result] == [
        "Prime Restaurants",
    ]


def test_search_by_code(
    db_session: Session,
) -> None:
    result = execute_search(
        db_session,
        "NILE",
        search_fields={
            "name",
            "code",
        },
    )

    assert [item.name for item in result] == [
        "Nile Hospitality",
    ]


def test_search_by_email(
    db_session: Session,
) -> None:
    result = execute_search(
        db_session,
        "alpha.com",
        search_fields={
            "name",
            "email",
        },
    )

    assert [item.name for item in result] == [
        "Alpha Foods",
    ]


def test_search_is_case_insensitive(
    db_session: Session,
) -> None:
    result = execute_search(
        db_session,
        "prime",
        search_fields={
            "name",
            "code",
        },
    )

    assert [item.name for item in result] == [
        "Prime Restaurants",
    ]


def test_search_supports_partial_match(
    db_session: Session,
) -> None:
    result = execute_search(
        db_session,
        "Hosp",
        search_fields={
            "name",
        },
    )

    assert [item.name for item in result] == [
        "Nile Hospitality",
    ]


def test_search_across_multiple_fields(
    db_session: Session,
) -> None:
    result = execute_search(
        db_session,
        "hotel",
        search_fields={
            "name",
            "code",
            "email",
        },
    )

    assert [item.name for item in result] == [
        "Nile Hospitality",
    ]


def test_none_search_returns_all_rows(
    db_session: Session,
) -> None:
    result = execute_search(
        db_session,
        None,
        search_fields={
            "name",
        },
    )

    assert len(result) == 3


def test_blank_search_returns_all_rows(
    db_session: Session,
) -> None:
    result = execute_search(
        db_session,
        "   ",
        search_fields={
            "name",
        },
    )

    assert len(result) == 3


def test_search_trims_whitespace(
    db_session: Session,
) -> None:
    result = execute_search(
        db_session,
        "  Alpha  ",
        search_fields={
            "name",
        },
    )

    assert [item.name for item in result] == [
        "Alpha Foods",
    ]


def test_search_returns_empty_when_no_match(
    db_session: Session,
) -> None:
    result = execute_search(
        db_session,
        "Unknown Company",
        search_fields={
            "name",
            "code",
        },
    )

    assert result == []


def test_reject_search_without_configured_fields(
    db_session: Session,
) -> None:
    with pytest.raises(
        QueryValidationException,
    ):
        execute_search(
            db_session,
            "Alpha",
            search_fields=None,
        )


def test_reject_empty_search_fields(
    db_session: Session,
) -> None:
    with pytest.raises(
        QueryValidationException,
    ):
        execute_search(
            db_session,
            "Alpha",
            search_fields=set(),
        )


def test_reject_unknown_search_field(
    db_session: Session,
) -> None:
    with pytest.raises(
        QueryValidationException,
    ):
        execute_search(
            db_session,
            "Alpha",
            search_fields={
                "unknown_field",
            },
        )


def test_reject_non_string_search_column(
    db_session: Session,
) -> None:
    with pytest.raises(
        QueryValidationException,
    ):
        execute_search(
            db_session,
            "1",
            search_fields={
                "id",
            },
        )


def test_reject_boolean_search_column(
    db_session: Session,
) -> None:
    with pytest.raises(
        QueryValidationException,
    ):
        execute_search(
            db_session,
            "true",
            search_fields={
                "is_active",
            },
        )


def test_reject_nested_search_field(
    db_session: Session,
) -> None:
    with pytest.raises(
        QueryValidationException,
    ):
        execute_search(
            db_session,
            "Alpha",
            search_fields={
                "tenant__name",
            },
        )


def test_reject_non_column_attribute(
    db_session: Session,
) -> None:
    with pytest.raises(
        QueryValidationException,
    ):
        execute_search(
            db_session,
            "Alpha",
            search_fields={
                "display_name",
            },
        )


def test_reject_non_string_search_value(
    db_session: Session,
) -> None:
    with pytest.raises(
        QueryValidationException,
    ):
        execute_search(
            db_session,
            123,
            search_fields={
                "name",
            },
        )