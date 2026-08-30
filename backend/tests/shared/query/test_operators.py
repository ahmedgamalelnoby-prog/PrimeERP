import pytest

from app.shared.query import (
    FilterOperator,
    QueryValidationException,
    parse_filter_field,
    parse_filter_operator,
)


@pytest.mark.parametrize(
    ("operator_value", "expected"),
    [
        ("eq", FilterOperator.EQ),
        ("ne", FilterOperator.NE),
        ("gt", FilterOperator.GT),
        ("gte", FilterOperator.GTE),
        ("lt", FilterOperator.LT),
        ("lte", FilterOperator.LTE),
        ("contains", FilterOperator.CONTAINS),
        ("startswith", FilterOperator.STARTS_WITH),
        ("endswith", FilterOperator.ENDS_WITH),
        ("in", FilterOperator.IN),
        ("between", FilterOperator.BETWEEN),
        ("isnull", FilterOperator.IS_NULL),
    ],
)
def test_parse_filter_operator_returns_expected_operator(
    operator_value: str,
    expected: FilterOperator,
) -> None:
    result = parse_filter_operator(operator_value)

    assert result is expected


def test_parse_filter_operator_is_case_insensitive() -> None:
    result = parse_filter_operator("CONTAINS")

    assert result is FilterOperator.CONTAINS


def test_parse_filter_operator_rejects_unknown_operator() -> None:
    with pytest.raises(QueryValidationException):
        parse_filter_operator("invalid")


def test_parse_filter_field_uses_eq_by_default() -> None:
    result = parse_filter_field("name")

    assert result.field_name == "name"
    assert result.operator is FilterOperator.EQ


def test_parse_filter_field_with_contains_operator() -> None:
    result = parse_filter_field("name__contains")

    assert result.field_name == "name"
    assert result.operator is FilterOperator.CONTAINS


def test_parse_filter_field_with_between_operator() -> None:
    result = parse_filter_field("created_at__between")

    assert result.field_name == "created_at"
    assert result.operator is FilterOperator.BETWEEN


def test_parse_nested_filter_field() -> None:
    result = parse_filter_field("customer__name__contains")

    assert result.field_name == "customer__name"
    assert result.operator is FilterOperator.CONTAINS


@pytest.mark.parametrize(
    "expression",
    [
        "",
        " ",
        "__contains",
        "name__",
        "name__unsupported",
    ],
)
def test_parse_filter_field_rejects_invalid_expression(
    expression: str,
) -> None:
    with pytest.raises(QueryValidationException):
        parse_filter_field(expression)