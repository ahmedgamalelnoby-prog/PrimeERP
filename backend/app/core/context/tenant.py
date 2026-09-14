from __future__ import annotations

from fastapi import HTTPException, status

from app.core.context.manager import get_request_context


def get_effective_tenant_id(user) -> int:
    """Return the tenant selected for this request.

    A platform administrator has no persisted tenant assignment, so the
    request context is authoritative for that user. Regular users normally
    carry their authenticated tenant on ``user.tenant_id``; their request
    context is populated with the same value by authentication.

    The helper also accepts lightweight domain/test objects that do not
    expose ``is_platform_admin``; when tenant context is missing entirely,
    those objects receive the same explicit "tenant context required"
    response used for platform-scoped operations.
    """
    context = get_request_context()
    tenant_id = user.tenant_id if user.tenant_id is not None else context.tenant_id

    if tenant_id is None:
        platform_flag = getattr(user, "is_platform_admin", None)
        if platform_flag is True or platform_flag is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant context is required for this operation",
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not assigned to a tenant",
        )

    return int(tenant_id)


__all__ = ["get_effective_tenant_id"]
