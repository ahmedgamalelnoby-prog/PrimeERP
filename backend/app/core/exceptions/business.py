from __future__ import annotations

from typing import Any, Optional

from app.core.exceptions.base import PrimeERPException


class ValidationException(PrimeERPException):
    def __init__(
        self,
        message: str = "Validation failed",
        *,
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(
            message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class NotFoundException(PrimeERPException):
    def __init__(
        self,
        message: str = "Record not found",
        *,
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(
            message,
            status_code=404,
            error_code="NOT_FOUND",
            details=details,
        )


class ConflictException(PrimeERPException):
    def __init__(
        self,
        message: str = "Record conflict",
        *,
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(
            message,
            status_code=409,
            error_code="CONFLICT",
            details=details,
        )


class BusinessRuleException(PrimeERPException):
    def __init__(
        self,
        message: str = "Business rule violation",
        *,
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(
            message,
            status_code=409,
            error_code="BUSINESS_RULE_ERROR",
            details=details,
        )


class AuthenticationException(PrimeERPException):
    def __init__(
        self,
        message: str = "Authentication failed",
        *,
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(
            message,
            status_code=401,
            error_code="AUTHENTICATION_ERROR",
            details=details,
        )


class AuthorizationException(PrimeERPException):
    def __init__(
        self,
        message: str = "Access denied",
        *,
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(
            message,
            status_code=403,
            error_code="AUTHORIZATION_ERROR",
            details=details,
        )


class TenantAccessException(AuthorizationException):
    def __init__(
        self,
        message: str = "Access to this tenant is not allowed",
        *,
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(
            message,
            details=details,
        )

        self.error_code = "TENANT_ACCESS_DENIED"


class SubscriptionException(PrimeERPException):
    def __init__(
        self,
        message: str = "Subscription is not active",
        *,
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(
            message,
            status_code=403,
            error_code="SUBSCRIPTION_ERROR",
            details=details,
        )


class PeriodClosedException(BusinessRuleException):
    def __init__(
        self,
        message: str = "Accounting period is closed",
        *,
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(
            message,
            details=details,
        )

        self.error_code = "ACCOUNTING_PERIOD_CLOSED"


class InvalidStatusTransitionException(
    BusinessRuleException
):
    def __init__(
        self,
        current_status: str,
        target_status: str,
    ) -> None:
        super().__init__(
            (
                f"Cannot change status from "
                f"{current_status} to {target_status}"
            ),
            details={
                "current_status": current_status,
                "target_status": target_status,
            },
        )

        self.error_code = "INVALID_STATUS_TRANSITION"