"""Shared constants for the canonical tax domain."""

from typing import Final

TAX_TYPES: Final[frozenset[str]] = frozenset({"vat", "wht", "custom"})

VAT_TAX_TYPE: Final[str] = "vat"
WHT_TAX_TYPE: Final[str] = "wht"
CUSTOM_TAX_TYPE: Final[str] = "custom"

MIN_TAX_RATE: Final[int] = 0
MAX_TAX_RATE: Final[int] = 100
