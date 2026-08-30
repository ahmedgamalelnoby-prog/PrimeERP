from __future__ import annotations

from typing import Any, Type

from sqlalchemy import or_
from sqlalchemy.orm import Query
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.sqltypes import String

from app.shared.query.exceptions import QueryValidationException


class SQLAlchemySearchAdapter:
    """
    Apply safe text search to a SQLAlchemy ORM query.

    The search term is matched against one or more configured
    string columns using case-insensitive partial matching.
    """

    def apply(
        self,
        query: Query,
        model: Type[Any],
        search: str | None,
        *,
        search_fields: set[str] | None,
    ) -> Query:
        """
        Apply search conditions to a SQLAlchemy query.

        Args:
            query:
                SQLAlchemy ORM query.

            model:
                SQLAlchemy model being queried.

            search:
                Search term entered by the user.

            search_fields:
                Explicit set of model fields that may be searched.

        Returns:
            The original query when search is empty, otherwise
            a query containing OR-based search conditions.
        """
        normalized_search = self._normalize_search(search)

        if normalized_search is None:
            return query

        columns = self._resolve_search_columns(
            model=model,
            search_fields=search_fields,
        )

        search_pattern = f"%{normalized_search}%"

        search_expressions = [
            column.ilike(search_pattern)
            for column in columns
        ]

        return query.filter(
            or_(*search_expressions)
        )

    @staticmethod
    def _normalize_search(
        search: str | None,
    ) -> str | None:
        """
        Normalize and validate the search term.
        """
        if search is None:
            return None

        if not isinstance(search, str):
            raise QueryValidationException(
                message="Search value must be a string.",
                details={
                    "received_type": type(search).__name__,
                },
            )

        normalized_search = search.strip()

        if not normalized_search:
            return None

        return normalized_search

    def _resolve_search_columns(
        self,
        model: Type[Any],
        search_fields: set[str] | None,
    ) -> list[InstrumentedAttribute]:
        """
        Resolve and validate searchable model columns.
        """
        if search_fields is None:
            raise QueryValidationException(
                message=(
                    "Search fields must be configured before "
                    "applying a search query."
                ),
                details={
                    "model": model.__name__,
                },
            )

        if not search_fields:
            raise QueryValidationException(
                message="Search fields cannot be empty.",
                details={
                    "model": model.__name__,
                },
            )

        columns: list[InstrumentedAttribute] = []

        for field_name in sorted(search_fields):
            column = self._get_searchable_column(
                model=model,
                field_name=field_name,
            )

            columns.append(column)

        return columns

    @staticmethod
    def _get_searchable_column(
        model: Type[Any],
        field_name: str,
    ) -> InstrumentedAttribute:
        """
        Resolve and validate one searchable SQLAlchemy column.
        """
        normalized_field_name = field_name.strip()

        if not normalized_field_name:
            raise QueryValidationException(
                message="Search field name cannot be empty.",
            )

        if "__" in normalized_field_name:
            raise QueryValidationException(
                message=(
                    f"Nested search field '{normalized_field_name}' "
                    "is not supported yet."
                ),
                details={
                    "field": normalized_field_name,
                },
            )

        if not hasattr(model, normalized_field_name):
            raise QueryValidationException(
                message=(
                    f"Model '{model.__name__}' does not contain "
                    f"search field '{normalized_field_name}'."
                ),
                details={
                    "model": model.__name__,
                    "field": normalized_field_name,
                },
            )

        column = getattr(
            model,
            normalized_field_name,
        )

        if not isinstance(
            column,
            InstrumentedAttribute,
        ):
            raise QueryValidationException(
                message=(
                    f"Attribute '{normalized_field_name}' on model "
                    f"'{model.__name__}' is not a searchable column."
                ),
                details={
                    "model": model.__name__,
                    "field": normalized_field_name,
                },
            )

        try:
            column_type = column.property.columns[0].type
        except (AttributeError, IndexError):
            raise QueryValidationException(
                message=(
                    f"Attribute '{normalized_field_name}' on model "
                    f"'{model.__name__}' is not a valid database column."
                ),
                details={
                    "model": model.__name__,
                    "field": normalized_field_name,
                },
            )

        if not isinstance(column_type, String):
            raise QueryValidationException(
                message=(
                    f"Search field '{normalized_field_name}' on model "
                    f"'{model.__name__}' must be a string column."
                ),
                details={
                    "model": model.__name__,
                    "field": normalized_field_name,
                    "column_type": type(column_type).__name__,
                },
            )

        return column