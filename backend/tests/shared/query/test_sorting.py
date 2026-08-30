from __future__ import annotations

import pytest
from sqlalchemy import Boolean, Integer, String, create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
)

from app.shared.query import (
    ParsedSortField,
    QueryValidationException,
    SortDirection,
    SQLAlchemySortingAdapter,
    parse_sort_expression,
    parse_sort_field,
)


class Base(DeclarativeBase):
    pass


class DemoCompany(Base):
    __tablename__ = "sorting_demo_companies"

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
                    name="Zulu Company",
                    code="C",
                    is_active=True,
                ),
                DemoCompany(
                    name="Alpha Company",
                    code="A",
                    is_active=False,
                ),
                DemoCompany(
                    name="Middle Company",
                    code="B",
                    is_active=True,
                ),
            ]
        )

        session.commit()

        yield session


def execute_sort(
    session: Session,
    sort: str | None,
    *,
    allowed_fields: set[str] | None = None,
) -> list[DemoCompany]:
    adapter = SQLAlchemySortingAdapter()

    query = session.query(DemoCompany)

    query = adapter.apply(
        query=query,
        model=DemoCompany,
        sort=sort,
        allowed_fields=allowed_fields,
    )

    return query.all()


def test_parse_sort_field_defaults_to_ascending() -> None:
    result = parse_sort_field("name")

    assert result == ParsedSortField(
        field_name="name",
        direction=SortDirection.ASC,
    )


def test_parse_sort_field_supports_descending() -> None:
    result = parse_sort_field("-created_at")

    assert result.field_name == "created_at"
    assert result.direction is SortDirection.DESC


def test_parse_sort_expression_supports_multiple_fields() -> None:
    result = parse_sort_expression(
        "name,-created_at,code"
    )

    assert len(result) == 3
    assert result[0].field_name == "name"
    assert result[0].direction is SortDirection.ASC
    assert result[1].field_name == "created_at"
    assert result[1].direction is SortDirection.DESC
    assert result[2].field_name == "code"


def test_parse_sort_expression_returns_empty_for_none() -> None:
    assert parse_sort_expression(None) == []


def test_parse_sort_expression_returns_empty_for_blank() -> None:
    assert parse_sort_expression("   ") == []


@pytest.mark.parametrize(
    "expression",
    [
        "",
        " ",
        "-",
        "--name",
        "name,",
        ",name",
    ],
)
def test_parse_sort_expression_rejects_invalid_values(
    expression: str,
) -> None:
    if expression.strip() == "":
        assert parse_sort_expression(expression) == []
        return

    with pytest.raises(QueryValidationException):
        parse_sort_expression(expression)


def test_parse_sort_expression_rejects_duplicates() -> None:
    with pytest.raises(QueryValidationException):
        parse_sort_expression(
            "name,-name"
        )


def test_apply_ascending_sort(
    db_session: Session,
) -> None:
    result = execute_sort(
        db_session,
        "name",
    )

    assert [item.name for item in result] == [
        "Alpha Company",
        "Middle Company",
        "Zulu Company",
    ]


def test_apply_descending_sort(
    db_session: Session,
) -> None:
    result = execute_sort(
        db_session,
        "-name",
    )

    assert [item.name for item in result] == [
        "Zulu Company",
        "Middle Company",
        "Alpha Company",
    ]


def test_apply_multiple_sort_fields(
    db_session: Session,
) -> None:
    result = execute_sort(
        db_session,
        "-is_active,name",
    )

    assert [item.name for item in result] == [
        "Middle Company",
        "Zulu Company",
        "Alpha Company",
    ]


def test_reject_unknown_sort_field(
    db_session: Session,
) -> None:
    with pytest.raises(QueryValidationException):
        execute_sort(
            db_session,
            "unknown_field",
        )


def test_reject_disallowed_sort_field(
    db_session: Session,
) -> None:
    with pytest.raises(QueryValidationException):
        execute_sort(
            db_session,
            "is_active",
            allowed_fields={
                "id",
                "name",
                "code",
            },
        )


def test_allow_configured_sort_field(
    db_session: Session,
) -> None:
    result = execute_sort(
        db_session,
        "code",
        allowed_fields={
            "id",
            "name",
            "code",
        },
    )

    assert [item.code for item in result] == [
        "A",
        "B",
        "C",
    ]


def test_reject_nested_sort_field(
    db_session: Session,
) -> None:
    with pytest.raises(QueryValidationException):
        execute_sort(
            db_session,
            "customer__name",
        )