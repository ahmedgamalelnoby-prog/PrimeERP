from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, Type

from sqlalchemy.orm import Query
from sqlalchemy.orm.attributes import InstrumentedAttribute

from app.shared.query.exceptions import QueryValidationException
from app.shared.query.operators import (
    FilterOperator,
    ParsedFilterField,
    parse_filter_field,
)


class SQLAlchemyFilterAdapter:
    """
    Apply generic filter expressions to a SQLAlchemy ORM Query.

    Example:
        filters = {
            "name__contains": "Prime",
            "is_active": True,
            "id__in": [1, 2, 3],
        }
    """

    def apply(
        self,
        query: Query,
        model: Type[Any],
        filters: Mapping[str, Any] | None,
    ) -> Query:
        """
        Apply filters to a SQLAlchemy query.
        """
        if not filters:
            return query

        for expression, value in filters.items():
            parsed_filter = parse_filter_field(expression)

            column = self._get_model_column(
                model=model,
                parsed_filter=parsed_filter,
            )

            condition = self._build_condition(
                column=column,
                operator=parsed_filter.operator,
                value=value,
                expression=expression,
            )

            query = query.filter(condition)

        return query

    def _get_model_column(
        self,
        model: Type[Any],
        parsed_filter: ParsedFilterField,
    ) -> InstrumentedAttribute:
        """
        Resolve a model column from a parsed filter field.
        """
        field_name = parsed_filter.field_name

        if "__" in field_name:
            raise QueryValidationException(
                message=(
                    f"Nested field filtering '{field_name}' "
                    "is not supported yet."
                ),
                details={
                    "field": field_name,
                },
            )

        if not hasattr(model, field_name):
            raise QueryValidationException(
                message=(
                    f"Model '{model.__name__}' does not contain "
                    f"filter field '{field_name}'."
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
                    f"'{model.__name__}' is not a filterable column."
                ),
                details={
                    "model": model.__name__,
                    "field": field_name,
                },
            )

        return column

    def _build_condition(
        self,
        column: InstrumentedAttribute,
        operator: FilterOperator,
        value: Any,
        expression: str,
    ) -> Any:
        """
        Build a SQLAlchemy filter condition.
        """
        if operator is FilterOperator.EQ:
            return self._apply_equal(column, value)

        if operator is FilterOperator.NE:
            return self._apply_not_equal(column, value)

        if operator is FilterOperator.GT:
            return column > value

        if operator is FilterOperator.GTE:
            return column >= value

        if operator is FilterOperator.LT:
            return column < value

        if operator is FilterOperator.LTE:
            return column <= value

        if operator is FilterOperator.CONTAINS:
            return column.ilike(
                f"%{self._require_string(value, expression)}%"
            )

        if operator is FilterOperator.STARTS_WITH:
            return column.ilike(
                f"{self._require_string(value, expression)}%"
            )

        if operator is FilterOperator.ENDS_WITH:
            return column.ilike(
                f"%{self._require_string(value, expression)}"
            )

        if operator is FilterOperator.IN:
            values = self._require_collection(
                value=value,
                expression=expression,
                operator=operator,
            )
            return column.in_(values)

        if operator is FilterOperator.BETWEEN:
            values = self._require_collection(
                value=value,
                expression=expression,
                operator=operator,
            )

            if len(values) != 2:
                raise QueryValidationException(
                    message=(
                        f"Filter '{expression}' requires exactly "
                        "two values."
                    ),
                    details={
                        "expression": expression,
                        "value": value,
                    },
                )

            return column.between(values[0], values[1])

        if operator is FilterOperator.IS_NULL:
            is_null = self._require_boolean(
                value=value,
                expression=expression,
            )

            if is_null:
                return column.is_(None)

            return column.is_not(None)

        raise QueryValidationException(
            message=(
                f"Filter operator '{operator.value}' "
                "is not implemented."
            ),
            details={
                "operator": operator.value,
                "expression": expression,
            },
        )

    @staticmethod
    def _apply_equal(
        column: InstrumentedAttribute,
        value: Any,
    ) -> Any:
        """
        Build an equality condition with proper NULL handling.
        """
        if value is None:
            return column.is_(None)

        if isinstance(value, bool):
            return column.is_(value)

        return column == value

    @staticmethod
    def _apply_not_equal(
        column: InstrumentedAttribute,
        value: Any,
    ) -> Any:
        """
        Build a non-equality condition with proper NULL handling.
        """
        if value is None:
            return column.is_not(None)

        if isinstance(value, bool):
            return column.is_not(value)

        return column != value

    @staticmethod
    def _require_string(
        value: Any,
        expression: str,
    ) -> str:
        """
        Ensure that a string operator receives a string value.
        """
        if not isinstance(value, str):
            raise QueryValidationException(
                message=(
                    f"Filter '{expression}' requires a string value."
                ),
                details={
                    "expression": expression,
                    "value": value,
                },
            )

        return value

    @staticmethod
    def _require_collection(
        value: Any,
        expression: str,
        operator: FilterOperator,
    ) -> list[Any]:
        """
        Ensure that IN and BETWEEN receive a collection.
        """
        if isinstance(value, (str, bytes)):
            raise QueryValidationException(
                message=(
                    f"Filter '{expression}' with operator "
                    f"'{operator.value}' requires a collection."
                ),
                details={
                    "expression": expression,
                    "value": value,
                },
            )

        if not isinstance(value, Iterable):
            raise QueryValidationException(
                message=(
                    f"Filter '{expression}' with operator "
                    f"'{operator.value}' requires a collection."
                ),
                details={
                    "expression": expression,
                    "value": value,
                },
            )

        values = list(value)

        if not values:
            raise QueryValidationException(
                message=(
                    f"Filter '{expression}' cannot use "
                    "an empty collection."
                ),
                details={
                    "expression": expression,
                },
            )

        return values

    @staticmethod
    def _require_boolean(
        value: Any,
        expression: str,
    ) -> bool:
        """
        Ensure that IS_NULL receives a boolean value.
        """
        if not isinstance(value, bool):
            raise QueryValidationException(
                message=(
                    f"Filter '{expression}' requires "
                    "a boolean value."
                ),
                details={
                    "expression": expression,
                    "value": value,
                },
            )

        return value