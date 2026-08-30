from __future__ import annotations

from typing import Any, Optional

from app.core.exceptions import PrimeERPException


class QueryValidationException(PrimeERPException):
    """
    Raised when a query, filter field, or filter operator is invalid.
    """

    status_code = 422
    error_code = "QUERY_VALIDATION_ERROR"

    def __init__(
        self,
        message: str,
        *,
        details: Optional[Any] = None,
    ) -> None:
        errors = [] if details is None else [{"details": details}]
        super().__init__(message=message, errors=errors)
