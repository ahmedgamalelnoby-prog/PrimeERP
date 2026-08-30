from __future__ import annotations

from uuid import UUID

from app.core.exceptions import ValidationException


def ensure_uuid(
    value: str,
    field_name: str = "UUID",
) -> UUID:
    """
    Validate and parse UUID.
    """
    try:
        return UUID(value)
    except ValueError as exc:
        raise ValidationException(
            f"{field_name} is not a valid UUID."
        ) from exc