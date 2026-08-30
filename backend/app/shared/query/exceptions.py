from __future__ import annotations

from typing import Any, Optional

from app.core.exceptions import PrimeERPException


class QueryValidationException(PrimeERPException):
    """
    Raised when a query, filter field, or filter operator is invalid.
    """

    def __init__(
        self,
        message: str,
        *,
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=422,
            error_code="QUERY_VALIDATION_ERROR",
            details=details,
        )