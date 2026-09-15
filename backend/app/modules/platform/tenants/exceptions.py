from app.core.exceptions import (
    BusinessException,
    ConflictException,
    NotFoundException,
)


class TenantNotFoundError(NotFoundException):
    error_code = "tenant_not_found"

    def __init__(self, identifier: int | str) -> None:
        super().__init__(f"Tenant '{identifier}' was not found.")


class TenantSlugAlreadyExistsError(ConflictException):
    error_code = "tenant_slug_already_exists"

    def __init__(self, slug: str) -> None:
        super().__init__(f"Tenant slug '{slug}' already exists.")


class TenantAlreadySuspendedError(BusinessException):
    error_code = "tenant_already_suspended"

    def __init__(self, tenant_id: int) -> None:
        super().__init__(f"Tenant '{tenant_id}' is already suspended.")


class TenantNotSuspendedError(BusinessException):
    error_code = "tenant_not_suspended"

    def __init__(self, tenant_id: int) -> None:
        super().__init__(f"Tenant '{tenant_id}' is not suspended.")


class InvalidTrialPeriodError(BusinessException):
    error_code = "invalid_trial_period"


class InvalidTenantStatusTransitionError(BusinessException):
    error_code = "invalid_tenant_status_transition"

    def __init__(self, current_status: str, target_status: str) -> None:
        if current_status == "no_active_subscription":
            message = "no_active_subscription: tenant has no current active subscription."
        else:
            message = f"Tenant status cannot change from '{current_status}' to '{target_status}'."
        super().__init__(message)
