from __future__ import annotations

from typing import Any


class PrimeERPException(Exception):
    status_code: int = 500
    error_code: str = "application_error"
    default_message: str = "An application error occurred."

    def __init__(
        self,
        message: str | None = None,
        *,
        errors: list[dict[str, Any]] | None = None,
    ) -> None:
        self.message = message or self.default_message
        self.errors = errors or []

        super().__init__(self.message)


class AppException(PrimeERPException):
    pass


class BadRequestException(AppException):
    status_code = 400
    error_code = "bad_request"
    default_message = "The request is invalid."


class UnauthorizedException(AppException):
    status_code = 401
    error_code = "unauthorized"
    default_message = "Authentication is required."


class ForbiddenException(AppException):
    status_code = 403
    error_code = "forbidden"
    default_message = "You do not have permission to perform this action."


class NotFoundException(AppException):
    status_code = 404
    error_code = "not_found"
    default_message = "The requested resource was not found."


class ConflictException(AppException):
    status_code = 409
    error_code = "conflict"
    default_message = "The resource conflicts with existing data."


class ValidationException(AppException):
    status_code = 422
    error_code = "validation_error"
    default_message = "Validation failed."


class BusinessException(AppException):
    status_code = 422
    error_code = "business_rule_error"
    default_message = "A business rule prevented the operation."