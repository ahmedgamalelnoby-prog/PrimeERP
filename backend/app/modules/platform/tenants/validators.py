import re
from datetime import datetime, timezone


SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def normalize_tenant_slug(value: str) -> str:
    slug = value.strip().lower().replace("_", "-").replace(" ", "-")

    while "--" in slug:
        slug = slug.replace("--", "-")

    slug = slug.strip("-")

    if not slug:
        raise ValueError("Tenant slug cannot be empty.")

    if not SLUG_PATTERN.fullmatch(slug):
        raise ValueError(
            "Tenant slug may contain lowercase letters, "
            "numbers and hyphens only."
        )

    return slug


def normalize_email(value: str) -> str:
    return value.strip().lower()


def normalize_country_code(value: str) -> str:
    code = value.strip().upper()

    if len(code) != 2:
        raise ValueError("Country code must contain exactly two letters.")

    return code


def normalize_currency_code(value: str) -> str:
    code = value.strip().upper()

    if len(code) != 3:
        raise ValueError("Currency code must contain exactly three letters.")

    return code


def utc_now() -> datetime:
    return datetime.now(timezone.utc)