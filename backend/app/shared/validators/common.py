from __future__ import annotations

from app.core.exceptions import ValidationException


def ensure_not_none(
    value: object,
    field_name: str,
) -> None:
    """
    Ensure that a value is not None.
    """
    if value is None:
        raise ValidationException(
            f"{field_name} cannot be None."
        )


def ensure_not_empty(
    value: str,
    field_name: str,
) -> None:
    """
    Ensure that a string is not empty.
    """
    if not value.strip():
        raise ValidationException(
            f"{field_name} cannot be empty."
        )


def ensure_positive(
    value: int | float,
    field_name: str,
) -> None:
    """
    Ensure value is greater than zero.
    """
    if value <= 0:
        raise ValidationException(
            f"{field_name} must be greater than zero."
        )