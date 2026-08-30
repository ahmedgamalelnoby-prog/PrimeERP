from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import HTTPException, Request, status


def extract_permission_codes(
    current_user: Any,
) -> set[str]:
    permission_codes: set[str] = set()

    direct_permissions = getattr(
        current_user,
        "permissions",
        None,
    )

    if direct_permissions:
        for permission in direct_permissions:
            if isinstance(permission, str):
                permission_codes.add(permission)
                continue

            code = getattr(
                permission,
                "code",
                None,
            )

            if code:
                permission_codes.add(
                    str(code)
                )

    role = getattr(
        current_user,
        "role",
        None,
    )

    role_permissions = getattr(
        role,
        "permissions",
        None,
    )

    if role_permissions:
        for permission in role_permissions:
            if isinstance(permission, str):
                permission_codes.add(permission)
                continue

            code = getattr(
                permission,
                "code",
                None,
            )

            if code:
                permission_codes.add(
                    str(code)
                )

    return permission_codes


def user_has_permission(
    current_user: Any,
    permission_code: str,
) -> bool:
    if getattr(
        current_user,
        "is_superuser",
        False,
    ):
        return True

    permissions = extract_permission_codes(
        current_user
    )

    return permission_code in permissions


def require_permission(
    permission_code: str,
) -> Callable[[Request], None]:
    """
    Generic request-state permission checker.

    This requires authentication middleware/dependency to set:
        request.state.current_user

    Do not use it in routers until current_user is placed
    on request.state by the authentication layer.
    """

    def dependency(
        request: Request,
    ) -> None:
        current_user = getattr(
            request.state,
            "current_user",
            None,
        )

        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication is required.",
            )

        if not user_has_permission(
            current_user,
            permission_code,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Missing required permission: "
                    f"{permission_code}"
                ),
            )

    return dependency