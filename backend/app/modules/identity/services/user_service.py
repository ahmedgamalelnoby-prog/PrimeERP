from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.services.base_service import BaseService
from app.modules.audit.service import record_audit_event
from app.modules.identity.models.user import User
from app.modules.identity.repositories.user_repository import (
    UserRepository,
    user_repository,
)
from app.modules.roles.models import Role
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

    def _validate_role(self, role_id: int | None) -> None:
        if role_id is None:
            return
        role = self.require_db().execute(
            select(Role).where(Role.id == role_id)
        ).scalar_one_or_none()
        if role is None or not role.is_active:
            raise ValueError("Selected role is inactive or unavailable.")

    def _resolve_write_tenant_id(self, tenant_id: int | None) -> int | None:
        """Never allow a tenant user to write another tenant's identity data."""
        current_user = self.current_user
        if getattr(current_user, "is_platform_admin", False):
            return tenant_id
        current_tenant_id = getattr(current_user, "tenant_id", None)
        if current_tenant_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Current user is not assigned to a tenant.",
            )
        if tenant_id is not None and tenant_id != current_tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cross-tenant identity access is not allowed.",
            )
        return current_tenant_id

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
        effective_tenant_id = self._resolve_write_tenant_id(tenant_id)
        current_user = self.current_user
        if not getattr(current_user, "is_platform_admin", False):
            is_superuser = False
            extra_data["is_platform_admin"] = False
        self._validate_role(role_id)
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
            record_audit_event(
                db,
                action="user.create",
                entity_type="user",
                entity_id=user.id,
                user_id=getattr(current_user, "id", None),
                tenant_id=effective_tenant_id,
                metadata={"username": user.username, "role_id": user.role_id, "is_active": user.is_active},
            )
            uow.commit()
        repository.refresh(db, user)
        return user

    def update_user(self, user_id: int, *, data: dict[str, Any], tenant_id: int | None = None) -> User:
        db = self.require_db()
        repository = self.require_repository()
        effective_tenant_id = self._resolve_write_tenant_id(tenant_id)
        with self.uow as uow:
            user = repository.get_by_id(db, user_id, tenant_id=effective_tenant_id, for_update=True)
            if user is None:
                raise LookupError("User was not found.")
            update_data = dict(data)
            if "role_id" in update_data:
                self._validate_role(update_data["role_id"])
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
            password_changed = "password" in update_data
            if password_changed:
                password = update_data.pop("password")
                if password:
                    update_data["hashed_password"] = password_service.hash_password(str(password))
            if not getattr(self.current_user, "is_platform_admin", False):
                update_data.pop("is_platform_admin", None)
                update_data.pop("is_superuser", None)
            protected_fields = {"id", "uuid", "tenant_id", "hashed_password", "created_at", "created_by"}
            update_data = {key: value for key, value in update_data.items() if key not in protected_fields}
            repository.update(db, user, data=update_data)
            record_audit_event(
                db,
                action="user.update",
                entity_type="user",
                entity_id=user.id,
                user_id=getattr(self.current_user, "id", None),
                tenant_id=effective_tenant_id,
                metadata={"changed_fields": sorted(update_data.keys()), "password_changed": password_changed},
            )
            uow.commit()
        repository.refresh(db, user)
        return user

    def set_active_status(self, user_id: int, *, is_active: bool, tenant_id: int | None = None) -> User:
        return self.update_user(user_id, tenant_id=tenant_id, data={"is_active": is_active})

    def reset_password(self, user_id: int, *, new_password: str, tenant_id: int | None = None, must_change_password: bool = True) -> User:
        db = self.require_db()
        repository = self.require_repository()
        effective_tenant_id = self._resolve_write_tenant_id(tenant_id)
        with self.uow as uow:
            user = repository.get_by_id(db, user_id, tenant_id=effective_tenant_id, for_update=True)
            if user is None:
                raise LookupError("User was not found.")
            repository.update(db, user, data={"hashed_password": password_service.hash_password(new_password), "must_change_password": must_change_password})
            record_audit_event(
                db,
                action="user.password_reset",
                entity_type="user",
                entity_id=user.id,
                user_id=getattr(self.current_user, "id", None),
                tenant_id=effective_tenant_id,
                metadata={"must_change_password": must_change_password},
            )
            uow.commit()
        repository.refresh(db, user)
        return user

    def soft_delete_user(self, user_id: int, *, tenant_id: int | None = None, deleted_by: int | None = None) -> User:
        db = self.require_db()
        repository = self.require_repository()
        effective_tenant_id = self._resolve_write_tenant_id(tenant_id)
        with self.uow as uow:
            user = repository.get_by_id(db, user_id, tenant_id=effective_tenant_id, for_update=True)
            if user is None:
                raise LookupError("User was not found.")
            repository.soft_delete(db, user, deleted_by=deleted_by)
            if hasattr(user, "is_active"):
                user.is_active = False
            record_audit_event(
                db,
                action="user.delete",
                entity_type="user",
                entity_id=user.id,
                user_id=deleted_by or getattr(self.current_user, "id", None),
                tenant_id=effective_tenant_id,
                metadata={"username": user.username},
            )
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
