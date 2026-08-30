from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final

from app.shared.query.exceptions import QueryValidationException


class FilterOperator(str, Enum):
    """
    Supported query filter operators.
    """

    EQ = "eq"
    NE = "ne"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"

    CONTAINS = "contains"
    STARTS_WITH = "startswith"
    ENDS_WITH = "endswith"

    IN = "in"
    BETWEEN = "between"
    IS_NULL = "isnull"

    def __str__(self) -> str:
        return self.value


DEFAULT_FILTER_OPERATOR: Final[FilterOperator] = FilterOperator.EQ

FILTER_SEPARATOR: Final[str] = "__"


@dataclass(frozen=True, slots=True)
class ParsedFilterField:
    """
    Parsed representation of a filter expression.

    Example:
        name__contains

    Result:
        field_name = "name"
        operator = FilterOperator.CONTAINS
    """

    field_name: str
    operator: FilterOperator


def parse_filter_operator(
    value: str,
) -> FilterOperator:
    """
    Convert a string value to a supported FilterOperator.

    Raises:
        QueryValidationException:
            If the provided operator is unsupported.
    """
    normalized_value = value.strip().lower()

    try:
        return FilterOperator(normalized_value)
    except ValueError as exc:
        supported_operators = ", ".join(
            operator.value for operator in FilterOperator
        )

        raise QueryValidationException(
            message=(
                f"Unsupported filter operator '{value}'. "
                f"Supported operators: {supported_operators}."
            )
        ) from exc


def parse_filter_field(
    expression: str,
) -> ParsedFilterField:
    """
    Parse a filter expression into a field name and operator.

    Examples:
        name
        name__contains
        created_at__between
        id__in
    """
    normalized_expression = expression.strip()

    if not normalized_expression:
        raise QueryValidationException(
            message="Filter field expression cannot be empty."
        )

    parts = normalized_expression.rsplit(
        FILTER_SEPARATOR,
        maxsplit=1,
    )

    if len(parts) == 1:
        field_name = parts[0]
        operator = DEFAULT_FILTER_OPERATOR
    else:
        field_name, operator_value = parts

        if not operator_value:
            raise QueryValidationException(
                message=(
                    f"Filter expression '{expression}' "
                    "does not contain a valid operator."
                )
            )

        operator = parse_filter_operator(operator_value)

    field_name = field_name.strip()

    if not field_name:
        raise QueryValidationException(
            message=(
                f"Filter expression '{expression}' "
                "does not contain a valid field name."
            )
        )

    return ParsedFilterField(
        field_name=field_name,
        operator=operator,
    )