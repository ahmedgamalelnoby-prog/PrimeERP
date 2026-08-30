from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)

from app.core.dependencies import get_user_service
from app.modules.identity.models.user import User
from app.modules.identity.schemas.user import (
    UserCreate,
    UserPasswordReset,
    UserResponse,
    UserStatusUpdate,
    UserUpdate,
)
from app.modules.identity.services.user_service import UserService
from app.core.schemas.pagination import (
    PaginatedResponse,
)

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


def require_admin(service: UserService) -> User:
    current_user = service.require_current_user()

    if not (
        current_user.is_superuser
        or current_user.is_platform_admin
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator permission is required.",
        )

    return current_user


def build_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        tenant_id=user.tenant_id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        address=user.address,
        profile_image=user.profile_image,
        preferred_language=user.preferred_language or "ar",
        role_id=user.role_id,
        role_name=(
            user.role.name
            if user.role is not None
            else None
        ),
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        is_platform_admin=user.is_platform_admin,
        is_deleted=user.is_deleted,
        must_change_password=user.must_change_password,
        last_login=user.last_login,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.get(
    "/",
    response_model=PaginatedResponse[UserResponse],
)
def list_users(
    search: str | None = Query(
        default=None,
        max_length=100,
    ),
    is_active: bool | None = Query(
        default=None,
    ),
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=25,
        ge=1,
        le=200,
    ),
    service: UserService = Depends(
        get_user_service
    ),
) -> PaginatedResponse[UserResponse]:
    require_admin(service)

    users, total = service.list_users_page(
        search=search,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )

    items = [
        build_user_response(user)
        for user in users
    ]

    return PaginatedResponse[UserResponse].create(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
def get_user(
    user_id: int,
    service: UserService = Depends(
        get_user_service
    ),
) -> UserResponse:
    require_admin(service)

    user = service.get_by_id(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User was not found.",
        )

    return build_user_response(user)


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    payload: UserCreate,
    service: UserService = Depends(
        get_user_service
    ),
) -> UserResponse:
    current_user = require_admin(service)

    tenant_id = payload.tenant_id

    if not current_user.is_platform_admin:
        tenant_id = current_user.tenant_id

    try:
        user = service.create_user(
            username=payload.username,
            email=str(payload.email),
            password=payload.password,
            tenant_id=tenant_id,
            full_name=payload.full_name,
            phone=payload.phone,
            role_id=payload.role_id,
            is_active=payload.is_active,
            is_superuser=payload.is_superuser,
            address=payload.address,
            profile_image=payload.profile_image,
            preferred_language=(
                payload.preferred_language
            ),
            is_platform_admin=(
                payload.is_platform_admin
                if current_user.is_platform_admin
                else False
            ),
            must_change_password=(
                payload.must_change_password
            ),
        )

        return build_user_response(user)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.put(
    "/{user_id}",
    response_model=UserResponse,
)
def update_user(
    user_id: int,
    payload: UserUpdate,
    service: UserService = Depends(
        get_user_service
    ),
) -> UserResponse:
    current_user = require_admin(service)

    update_data = payload.model_dump(
        exclude_unset=True
    )

    if not current_user.is_platform_admin:
        update_data.pop(
            "is_platform_admin",
            None,
        )

    try:
        user = service.update_user(
            user_id,
            data=update_data,
        )

        return build_user_response(user)

    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{user_id}/status",
    response_model=UserResponse,
)
def update_user_status(
    user_id: int,
    payload: UserStatusUpdate,
    service: UserService = Depends(
        get_user_service
    ),
) -> UserResponse:
    current_user = require_admin(service)

    if (
        current_user.id == user_id
        and not payload.is_active
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "You cannot deactivate your own account."
            ),
        )

    try:
        user = service.set_active_status(
            user_id,
            is_active=payload.is_active,
        )

        return build_user_response(user)

    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/{user_id}/reset-password",
    response_model=UserResponse,
)
def reset_user_password(
    user_id: int,
    payload: UserPasswordReset,
    service: UserService = Depends(
        get_user_service
    ),
) -> UserResponse:
    require_admin(service)

    try:
        user = service.reset_password(
            user_id,
            new_password=payload.new_password,
            must_change_password=(
                payload.must_change_password
            ),
        )

        return build_user_response(user)

    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_user(
    user_id: int,
    service: UserService = Depends(
        get_user_service
    ),
) -> Response:
    current_user = require_admin(service)

    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "You cannot delete your own account."
            ),
        )

    try:
        service.soft_delete_user(
            user_id,
            deleted_by=current_user.id,
        )

    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )


@router.post(
    "/{user_id}/restore",
    response_model=UserResponse,
)
def restore_user(
    user_id: int,
    service: UserService = Depends(
        get_user_service
    ),
) -> UserResponse:
    require_admin(service)

    try:
        user = service.restore_user(user_id)

        return build_user_response(user)

    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc