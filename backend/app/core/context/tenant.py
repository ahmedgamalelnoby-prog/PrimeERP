from __future__ import annotations

from fastapi import HTTPException, status

from app.core.context.manager import get_request_context
from app.modules.identity.models import User


def get_effective_tenant_id(user: User) -> int:
    """Return the tenant selected for this request.

    Regular users are permanently bound to ``user.tenant_id``.
    Platform admins may operate on a tenant only after selecting it for
    the current request (currently through the X-Tenant-ID header, resolved
    by the authentication dependency). The selected tenant lives only in
    RequestContext and never mutates the platform-admin database record.
    """
    context = get_request_context()
    tenant_id = context.tenant_id if user.is_platform_admin else user.tenant_id

    if tenant_id is None:
        if user.is_platform_admin:
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
