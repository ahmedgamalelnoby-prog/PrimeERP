from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.services.base_service import BaseService
from app.modules.identity.models.user import User
from app.modules.identity.repositories.user_repository import (
    UserRepository,
    user_repository,
)
from app.modules.identity.services.password_service import (
    password_service,
)
from app.modules.saas.entitlements import enforce_user_limit


class UserService(BaseService[UserRepository]):
    def __init__(
        self,
        *,
        db: Session | None = None,
        current_user: Any | None = None,
        current_tenant: Any | None = None,
        repository: UserRepository = user_repository,
    ) -> None:
        super().__init__(
            repository=repository,
            db=db,
            current_user=current_user,
            current_tenant=current_tenant,
        )

    def get_by_id(
        self,
        user_id: int,
        *,
        tenant_id: int | None = None,
        include_deleted: bool = False,
    ) -> User | None:
        db = self.require_db()
        repository = self.require_repository()
        effective_tenant_id = self._resolve_tenant_id(tenant_id)
        return repository.get_by_id(
            db,
            user_id,
            tenant_id=effective_tenant_id,
            include_deleted=include_deleted,
        )

    def _enforce_user_limit(self, tenant_id: int | None) -> None:
        current_user = self.current_user
        if tenant_id is None or getattr(current_user, "is_platform_admin", False):
            return
        db = self.require_db()
        enforce_user_limit(db, tenant_id)

    def create_user(
        self,
        *,
        username: str,
        email: str,
        password: str,
        tenant_id: int | None = None,
        full_name: str | None = None,
        phone: str | None = None,
        role_id: int | None = None,
        is_active: bool = True,
        is_superuser: bool = False,
        **extra_data: Any,
    ) -> User:
        db = self.require_db()
        repository = self.require_repository()
        effective_tenant_id = self._resolve_tenant_id(tenant_id)
        current_user = self.current_user
        if not getattr(current_user, "is_platform_admin", False):
            is_superuser = False
            extra_data["is_platform_admin"] = False
        self._enforce_user_limit(effective_tenant_id)

        normalized_username = username.strip().lower()
        normalized_email = email.strip().lower()
        if repository.get_by_username(db, normalized_username, tenant_id=effective_tenant_id, include_deleted=True):
            raise ValueError("Username already exists for this tenant.")
        if repository.get_by_email(db, normalized_email, tenant_id=effective_tenant_id, include_deleted=True):
            raise ValueError("Email already exists for this tenant.")

        user_data: dict[str, Any] = {
            "username": normalized_username,
            "email": normalized_email,
            "hashed_password": password_service.hash_password(password),
            "full_name": full_name,
            "phone": phone,
            "role_id": role_id,
            "tenant_id": effective_tenant_id,
            "is_active": is_active,
            "is_superuser": is_superuser,
            **extra_data,
        }
        user_data = {key: value for key, value in user_data.items() if value is not None}

        with self.uow as uow:
            user = repository.create(db, data=user_data)
            uow.commit()
        repository.refresh(db, user)
        return user

    def update_user(self, user_id: int, *, data: dict[str, Any], tenant_id: int | None = None) -> User:
        db = self.require_db()
        repository = self.require_repository()
        effective_tenant_id = self._resolve_tenant_id(tenant_id)
        with self.uow as uow:
            user = repository.get_by_id(db, user_id, tenant_id=effective_tenant_id, for_update=True)
            if user is None:
                raise LookupError("User was not found.")
            update_data = dict(data)
            if "username" in update_data:
                new_username = str(update_data["username"]).strip().lower()
                existing_user = repository.get_by_username(db, new_username, tenant_id=effective_tenant_id, include_deleted=True)
                if existing_user is not None and existing_user.id != user.id:
                    raise ValueError("Username already exists for this tenant.")
                update_data["username"] = new_username
            if "email" in update_data:
                new_email = str(update_data["email"]).strip().lower()
                existing_user = repository.get_by_email(db, new_email, tenant_id=effective_tenant_id, include_deleted=True)
                if existing_user is not None and existing_user.id != user.id:
                    raise ValueError("Email already exists for this tenant.")
                update_data["email"] = new_email
            if "password" in update_data:
                password = update_data.pop("password")
                if password:
                    update_data["hashed_password"] = password_service.hash_password(str(password))
            if not getattr(self.current_user, "is_platform_admin", False):
                update_data.pop("is_platform_admin", None)
                update_data.pop("is_superuser", None)
            protected_fields = {"id", "uuid", "tenant_id", "hashed_password", "created_at", "created_by"}
            update_data = {key: value for key, value in update_data.items() if key not in protected_fields}
            repository.update(db, user, data=update_data)
            uow.commit()
        repository.refresh(db, user)
        return user

    def set_active_status(self, user_id: int, *, is_active: bool, tenant_id: int | None = None) -> User:
        return self.update_user(user_id, tenant_id=tenant_id, data={"is_active": is_active})

    def reset_password(self, user_id: int, *, new_password: str, tenant_id: int | None = None, must_change_password: bool = True) -> User:
        db = self.require_db()
        repository = self.require_repository()
        effective_tenant_id = self._resolve_tenant_id(tenant_id)
        with self.uow as uow:
            user = repository.get_by_id(db, user_id, tenant_id=effective_tenant_id, for_update=True)
            if user is None:
                raise LookupError("User was not found.")
            repository.update(db, user, data={"hashed_password": password_service.hash_password(new_password), "must_change_password": must_change_password})
            uow.commit()
        repository.refresh(db, user)
        return user

    def soft_delete_user(self, user_id: int, *, tenant_id: int | None = None, deleted_by: int | None = None) -> User:
        db = self.require_db()
        repository = self.require_repository()
        effective_tenant_id = self._resolve_tenant_id(tenant_id)
        with self.uow as uow:
            user = repository.get_by_id(db, user_id, tenant_id=effective_tenant_id, for_update=True)
            if user is None:
                raise LookupError("User was not found.")
            repository.soft_delete(db, user, deleted_by=deleted_by)
            if hasattr(user, "is_active"):
                user.is_active = False
            uow.commit()
        repository.refresh(db, user)
        return user

    def list_users(self, *, tenant_id: int | None = None, search: str | None = None, is_active: bool | None = None, skip: int = 0, limit: int = 50) -> list[User]:
        db = self.require_db()
        repository = self.require_repository()
        effective_tenant_id = self._resolve_tenant_id(tenant_id)
        return repository.list_users(db, tenant_id=effective_tenant_id, search=search, is_active=is_active, skip=max(skip, 0), limit=min(max(limit, 1), 200))

    def list_users_page(self, *, tenant_id: int | None = None, search: str | None = None, is_active: bool | None = None, page: int = 1, page_size: int = 25) -> tuple[list[User], int]:
        db = self.require_db()
        repository = self.require_repository()
        effective_tenant_id = self._resolve_tenant_id(tenant_id)
        safe_page = max(page, 1)
        safe_page_size = min(max(page_size, 1), 200)
        skip = (safe_page - 1) * safe_page_size
        users = repository.list_users(db, tenant_id=effective_tenant_id, search=search, is_active=is_active, skip=skip, limit=safe_page_size)
        total = repository.count_users(db, tenant_id=effective_tenant_id, search=search, is_active=is_active)
        return users, total

    def _resolve_tenant_id(self, tenant_id: int | None) -> int | None:
        if tenant_id is not None:
            return tenant_id
        tenant = self.current_tenant
        if tenant is None:
            return None
        if isinstance(tenant, int):
            return tenant
        return getattr(tenant, "id", None)
