from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any

from app.modules.platform.plans.constants import (
    PLAN_CODE_MAX_LENGTH,
    PLAN_CODE_MIN_LENGTH,
    PLAN_CODE_PATTERN,
)
from app.modules.platform.plans.exceptions import (
    InvalidPlanPriceError,
    PlanValidationError,
)


def normalize_plan_code(value: str) -> str:
    code = value.strip().lower()

    code = re.sub(
        r"\s+",
        "_",
        code,
    )

    if not code:
        raise PlanValidationError(
            "Plan code is required."
        )

    if len(code) < PLAN_CODE_MIN_LENGTH:
        raise PlanValidationError(
            f"Plan code must contain at least "
            f"{PLAN_CODE_MIN_LENGTH} characters."
        )

    if len(code) > PLAN_CODE_MAX_LENGTH:
        raise PlanValidationError(
            f"Plan code cannot exceed "
            f"{PLAN_CODE_MAX_LENGTH} characters."
        )

    if re.fullmatch(
        PLAN_CODE_PATTERN,
        code,
    ) is None:
        raise PlanValidationError(
            "Plan code must start with a lowercase letter and may only "
            "contain lowercase letters, numbers, underscores and hyphens."
        )

    return code


def normalize_plan_name(value: str) -> str:
    name = " ".join(
        value.strip().split()
    )

    if not name:
        raise PlanValidationError(
            "Plan name is required."
        )

    return name


def normalize_optional_text(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    normalized = " ".join(
        value.strip().split()
    )

    return normalized or None


def normalize_price(
    value: Any,
    *,
    field_name: str,
) -> Decimal:
    if value is None:
        return Decimal("0.00")

    try:
        price = Decimal(
            str(value)
        )
    except (
        InvalidOperation,
        TypeError,
        ValueError,
    ) as exc:
        raise InvalidPlanPriceError(
            f"{field_name} must be a valid decimal number."
        ) from exc

    if not price.is_finite():
        raise InvalidPlanPriceError(
            f"{field_name} must be a finite number."
        )

    if price < Decimal("0"):
        raise InvalidPlanPriceError(
            f"{field_name} cannot be negative."
        )

    return price.quantize(
        Decimal("0.01")
    )


def validate_plan_prices(
    *,
    monthly_price: Any,
    yearly_price: Any,
    is_free: bool,
) -> tuple[Decimal, Decimal]:
    normalized_monthly_price = normalize_price(
        monthly_price,
        field_name="monthly_price",
    )

    normalized_yearly_price = normalize_price(
        yearly_price,
        field_name="yearly_price",
    )

    if is_free and (
        normalized_monthly_price > Decimal("0")
        or normalized_yearly_price > Decimal("0")
    ):
        raise InvalidPlanPriceError(
            "A free plan must have monthly and yearly prices equal to zero."
        )

    return (
        normalized_monthly_price,
        normalized_yearly_price,
    )


def validate_yearly_price(
    *,
    monthly_price: Decimal,
    yearly_price: Decimal,
) -> None:
    if (
        monthly_price > Decimal("0")
        and yearly_price > Decimal("0")
        and yearly_price > monthly_price * Decimal("12")
    ):
        raise InvalidPlanPriceError(
            "Yearly price cannot exceed twelve times the monthly price."
        )


def validate_plan_flags(
    *,
    is_free: bool,
    is_custom: bool,
    is_public: bool,
) -> None:
    if is_free and is_custom:
        raise PlanValidationError(
            "A plan cannot be both free and custom."
        )

    if is_custom and is_public:
        raise PlanValidationError(
            "A custom plan should not be publicly available."
        )