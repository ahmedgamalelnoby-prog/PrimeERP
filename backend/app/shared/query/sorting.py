from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Final, Type

from sqlalchemy.orm import Query
from sqlalchemy.orm.attributes import InstrumentedAttribute

from app.shared.query.exceptions import QueryValidationException


SORT_SEPARATOR: Final[str] = ","
DESCENDING_PREFIX: Final[str] = "-"


class SortDirection(str, Enum):
    """
    Supported sorting directions.
    """

    ASC = "asc"
    DESC = "desc"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class ParsedSortField:
    """
    Parsed representation of one sort field.

    Examples:
        name
        -created_at
    """

    field_name: str
    direction: SortDirection


def parse_sort_field(
    expression: str,
) -> ParsedSortField:
    """
    Parse a single sort expression.

    Examples:
        name -> ASC
        -created_at -> DESC
    """
    normalized_expression = expression.strip()

    if not normalized_expression:
        raise QueryValidationException(
            message="Sort field expression cannot be empty.",
        )

    direction = SortDirection.ASC
    field_name = normalized_expression

    if normalized_expression.startswith(DESCENDING_PREFIX):
        direction = SortDirection.DESC
        field_name = normalized_expression[1:].strip()

    if not field_name:
        raise QueryValidationException(
            message=(
                f"Sort expression '{expression}' "
                "does not contain a valid field name."
            ),
            details={
                "expression": expression,
            },
        )

    if field_name.startswith(DESCENDING_PREFIX):
        raise QueryValidationException(
            message=(
                f"Sort expression '{expression}' "
                "contains an invalid direction prefix."
            ),
            details={
                "expression": expression,
            },
        )

    return ParsedSortField(
        field_name=field_name,
        direction=direction,
    )


def parse_sort_expression(
    expression: str | None,
) -> list[ParsedSortField]:
    """
    Parse a comma-separated sorting expression.

    Example:
        name,-created_at,code
    """
    if expression is None:
        return []

    normalized_expression = expression.strip()

    if not normalized_expression:
        return []

    raw_fields = normalized_expression.split(SORT_SEPARATOR)

    parsed_fields = [
        parse_sort_field(raw_field)
        for raw_field in raw_fields
    ]

    field_names = [
        parsed_field.field_name
        for parsed_field in parsed_fields
    ]

    duplicates = {
        field_name
        for field_name in field_names
        if field_names.count(field_name) > 1
    }

    if duplicates:
        duplicate_names = ", ".join(sorted(duplicates))

        raise QueryValidationException(
            message=(
                "Duplicate sort fields are not allowed: "
                f"{duplicate_names}."
            ),
            details={
                "duplicates": sorted(duplicates),
            },
        )

    return parsed_fields


class SQLAlchemySortingAdapter:
    """
    Apply safe sorting expressions to a SQLAlchemy ORM Query.
    """

    def apply(
        self,
        query: Query,
        model: Type[Any],
        sort: str | None,
        *,
        allowed_fields: set[str] | None = None,
    ) -> Query:
        """
        Apply sorting to a SQLAlchemy ORM query.
        """
        parsed_fields = parse_sort_expression(sort)

        if not parsed_fields:
            return query

        order_by_expressions = []

        for parsed_field in parsed_fields:
            column = self._get_model_column(
                model=model,
                field_name=parsed_field.field_name,
                allowed_fields=allowed_fields,
            )

            if parsed_field.direction is SortDirection.DESC:
                order_by_expressions.append(column.desc())
            else:
                order_by_expressions.append(column.asc())

        return query.order_by(*order_by_expressions)

    @staticmethod
    def _get_model_column(
        model: Type[Any],
        field_name: str,
        allowed_fields: set[str] | None,
    ) -> InstrumentedAttribute:
        """
        Resolve and validate a sortable model column.
        """
        if "__" in field_name:
            raise QueryValidationException(
                message=(
                    f"Nested sorting field '{field_name}' "
                    "is not supported yet."
                ),
                details={
                    "field": field_name,
                },
            )

        if allowed_fields is not None and field_name not in allowed_fields:
            raise QueryValidationException(
                message=(
                    f"Sorting by field '{field_name}' "
                    "is not allowed."
                ),
                details={
                    "field": field_name,
                    "allowed_fields": sorted(allowed_fields),
                },
            )

        if not hasattr(model, field_name):
            raise QueryValidationException(
                message=(
                    f"Model '{model.__name__}' does not contain "
                    f"sorting field '{field_name}'."
                ),
                details={
                    "model": model.__name__,
                    "field": field_name,
                },
            )

        column = getattr(model, field_name)

        if not isinstance(column, InstrumentedAttribute):
            raise QueryValidationException(
                message=(
                    f"Attribute '{field_name}' on model "
                    f"'{model.__name__}' is not a sortable column."
                ),
                details={
                    "model": model.__name__,
                    "field": field_name,
                },
            )

        return column