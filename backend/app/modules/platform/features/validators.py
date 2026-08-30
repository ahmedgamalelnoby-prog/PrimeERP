from decimal import Decimal, InvalidOperation
from typing import Any

from .constants import FeatureValueType


TRUE_VALUES = {
    "true",
    "1",
    "yes",
    "on",
    "enabled",
}

FALSE_VALUES = {
    "false",
    "0",
    "no",
    "off",
    "disabled",
}


def normalize_feature_value(
    value_type: FeatureValueType | str,
    value: Any,
) -> str:
    """
    Validates and converts a feature value into its stored string format.
    """

    normalized_type = FeatureValueType(value_type)

    if value is None:
        raise ValueError("Feature value cannot be null.")

    if normalized_type == FeatureValueType.BOOLEAN:
        if isinstance(value, bool):
            return "true" if value else "false"

        normalized_value = str(value).strip().lower()

        if normalized_value in TRUE_VALUES:
            return "true"

        if normalized_value in FALSE_VALUES:
            return "false"

        raise ValueError(
            "Boolean value must be true or false."
        )

    if normalized_type == FeatureValueType.INTEGER:
        try:
            integer_value = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Integer feature value is invalid."
            ) from exc

        return str(integer_value)

    if normalized_type == FeatureValueType.DECIMAL:
        try:
            decimal_value = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValueError(
                "Decimal feature value is invalid."
            ) from exc

        if not decimal_value.is_finite():
            raise ValueError(
                "Decimal feature value must be finite."
            )

        return format(decimal_value.normalize(), "f")

    if normalized_type == FeatureValueType.TEXT:
        text_value = str(value).strip()

        if not text_value:
            raise ValueError(
                "Text feature value cannot be empty."
            )

        if len(text_value) > 255:
            raise ValueError(
                "Text feature value cannot exceed 255 characters."
            )

        return text_value

    raise ValueError(
        f"Unsupported feature value type: {normalized_type}"
    )