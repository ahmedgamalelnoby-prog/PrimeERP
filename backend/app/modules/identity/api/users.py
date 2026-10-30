from pydantic import BaseModel, Field, model_validator
from sqlalchemy import delete, select

from app.modules.audit.service import record_audit_event

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)

from app.core.dependencies import get_user_service
from app.core.permissions import require_permission
from app.core.permissions.checker import user_has_permission
from app.modules.identity.models.user import User
from app.modules.identity.schemas.user import (
    UserCreate,
    UserPasswordReset,
    UserResponse,
    UserStatusUpdate,
    UserUpdate,
)
from app.modules.identity.services.user_service import UserService
from app.core.schemas.pagination import PaginatedResponse
from app.modules.saas.entitlements import enforce_user_limit
from app.modules.companies.models import Company, user_company_access
from app.modules.companies.access import assigned_company_ids

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


class UserCompanyAccessUpdate(BaseModel):
    company_ids: list[int] = Field(min_length=1, max_length=500)
    default_company_id: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_company_selection(self):
        if len(self.company_ids) != len(set(self.company_ids)):
            raise ValueError("Company IDs must be unique")
        if self.default_company_id not in self.company_ids:
            raise ValueError("Default company must be included in company_ids")
        if any(company_id <= 0 for company_id in self.company_ids):
            raise ValueError("Company IDs must be positive")
        return self


def require_admin(service: UserService) -> User:
    current_user = service.require_current_user()
    if current_user.is_platform_admin:
        return current_user
    if user_has_permission(current_user, "users.access", service.require_db()):
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="User administration permission is required.",
    )


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
        role_name=user.role.name if user.role is not None else None,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        is_platform_admin=user.is_platform_admin,
        is_deleted=user.is_deleted,
        must_change_password=user.must_change_password,
        last_login=user.last_login,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.get("/{user_id}/companies/available", dependencies=[Depends(require_permission("users.access"))])
def get_available_user_companies(user_id: int, service: UserService = Depends(get_user_service)):
    current_user = require_admin(service)
    target = service.get_by_id(user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User was not found.")
    tenant_id = target.tenant_id
    if tenant_id is None or (not current_user.is_platform_admin and tenant_id != current_user.tenant_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User was not found.")
    db = service.require_db()
    companies = db.scalars(
        select(Company)
        .where(Company.tenant_id == tenant_id, Company.is_active.is_(True))
        .order_by(Company.name, Company.id)
    ).all()
    return [{"id": company.id, "name": company.name, "code": company.code} for company in companies]


@router.get("/{user_id}/companies", dependencies=[Depends(require_permission("users.access"))])
def get_user_company_access(user_id: int, service: UserService = Depends(get_user_service)):
    current_user = require_admin(service)
    target = service.get_by_id(user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User was not found.")
    if current_user.is_platform_admin:
        tenant_id = target.tenant_id
    else:
        tenant_id = current_user.tenant_id
    if tenant_id is None or target.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User was not found.")
    db = service.require_db()
    company_ids = assigned_company_ids(db, target.id, tenant_id)
    default_id = db.scalar(
        select(user_company_access.c.company_id).where(
            user_company_access.c.user_id == target.id,
            user_company_access.c.is_default.is_(True),
        )
    )
    return {"user_id": target.id, "company_ids": company_ids, "default_company_id": default_id}


@router.put("/{user_id}/companies", dependencies=[Depends(require_permission("users.write"))])
def update_user_company_access(
    user_id: int,
    payload: UserCompanyAccessUpdate,
    service: UserService = Depends(get_user_service),
):
    current_user = require_admin(service)
    if not current_user.is_platform_admin and not user_has_permission(
        current_user, "users.write", service.require_db()
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User write permission is required.")
    target = service.get_by_id(user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User was not found.")
    tenant_id = target.tenant_id
    if tenant_id is None or (not current_user.is_platform_admin and tenant_id != current_user.tenant_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User was not found.")

    db = service.require_db()
    companies = list(db.scalars(
        select(Company).where(
            Company.id.in_(payload.company_ids),
            Company.tenant_id == tenant_id,
            Company.is_active.is_(True),
        )
    ).all())
    if len(companies) != len(payload.company_ids):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Every selected company must be active and belong to the user's tenant.",
        )

    try:
        db.execute(delete(user_company_access).where(user_company_access.c.user_id == target.id))
        db.execute(
            user_company_access.insert(),
            [
                {
                    "user_id": target.id,
                    "company_id": company_id,
                    "is_default": company_id == payload.default_company_id,
                }
                for company_id in payload.company_ids
            ],
        )
        record_audit_event(
            db,
            action="user.company_access_updated",
            entity_type="user",
            entity_id=target.id,
            user_id=current_user.id,
            tenant_id=tenant_id,
            metadata={
                "company_ids": sorted(payload.company_ids),
                "default_company_id": payload.default_company_id,
            },
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "user_id": target.id,
        "company_ids": payload.company_ids,
        "default_company_id": payload.default_company_id,
    }


@router.get("/", response_model=PaginatedResponse[UserResponse])
def list_users(
    search: str | None = Query(default=None, max_length=100),
    is_active: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
    service: UserService = Depends(get_user_service),
) -> PaginatedResponse[UserResponse]:
    require_admin(service)
    users, total = service.list_users_page(search=search, is_active=is_active, page=page, page_size=page_size)
    return PaginatedResponse[UserResponse].create(
        items=[build_user_response(user) for user in users],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, service: UserService = Depends(get_user_service)) -> UserResponse:
    require_admin(service)
    user = service.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User was not found.")
    return build_user_response(user)


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("users.write"))])
def create_user(payload: UserCreate, service: UserService = Depends(get_user_service)) -> UserResponse:
    current_user = require_admin(service)
    if not user_has_permission(current_user, "users.write", service.require_db()) and not current_user.is_platform_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User write permission is required.")
    tenant_id = payload.tenant_id if current_user.is_platform_admin else current_user.tenant_id
    if tenant_id is not None and not current_user.is_platform_admin:
        enforce_user_limit(service.require_db(), tenant_id)
    try:
        user = service.create_user(
            username=payload.username,
            email=str(payload.email),
            password=payload.password,
            tenant_id=tenant_id,
            full_name=payload.full_name,
            phone=payload.phone,
            address=payload.address,
            profile_image=payload.profile_image,
            preferred_language=payload.preferred_language,
            role_id=payload.role_id,
            is_active=payload.is_active,
            is_superuser=payload.is_superuser if current_user.is_platform_admin else False,
            is_platform_admin=payload.is_platform_admin if current_user.is_platform_admin else False,
            must_change_password=payload.must_change_password,
        )
        return build_user_response(user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.put("/{user_id}", response_model=UserResponse, dependencies=[Depends(require_permission("users.write"))])
def update_user(user_id: int, payload: UserUpdate, service: UserService = Depends(get_user_service)) -> UserResponse:
    current_user = require_admin(service)
    if not user_has_permission(current_user, "users.write", service.require_db()) and not current_user.is_platform_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User write permission is required.")
    update_data = payload.model_dump(exclude_unset=True)
    if not current_user.is_platform_admin:
        update_data.pop("is_platform_admin", None)
        update_data.pop("is_superuser", None)
    try:
        return build_user_response(service.update_user(user_id, data=update_data))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.patch("/{user_id}/status", response_model=UserResponse, dependencies=[Depends(require_permission("users.write"))])
def update_user_status(user_id: int, payload: UserStatusUpdate, service: UserService = Depends(get_user_service)) -> UserResponse:
    current_user = require_admin(service)
    if not user_has_permission(current_user, "users.write", service.require_db()) and not current_user.is_platform_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User write permission is required.")
    if current_user.id == user_id and not payload.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot deactivate your own account.")
    try:
        return build_user_response(service.set_active_status(user_id, is_active=payload.is_active))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{user_id}/reset-password", response_model=UserResponse, dependencies=[Depends(require_permission("users.write"))])
def reset_user_password(user_id: int, payload: UserPasswordReset, service: UserService = Depends(get_user_service)) -> UserResponse:
    current_user = require_admin(service)
    if not user_has_permission(current_user, "users.write", service.require_db()) and not current_user.is_platform_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User write permission is required.")
    try:
        return build_user_response(service.reset_password(user_id, new_password=payload.new_password, must_change_password=payload.must_change_password))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permission("users.write"))])
def delete_user(user_id: int, service: UserService = Depends(get_user_service)) -> Response:
    current_user = require_admin(service)
    if not user_has_permission(current_user, "users.write", service.require_db()) and not current_user.is_platform_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User write permission is required.")
    if current_user.id == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot delete your own account.")
    try:
        service.soft_delete_user(user_id, deleted_by=current_user.id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{user_id}/restore", response_model=UserResponse, dependencies=[Depends(require_permission("users.write"))])
def restore_user(user_id: int, service: UserService = Depends(get_user_service)) -> UserResponse:
    current_user = require_admin(service)
    if not user_has_permission(current_user, "users.write", service.require_db()) and not current_user.is_platform_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User write permission is required.")
    try:
        return build_user_response(service.restore_user(user_id))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
