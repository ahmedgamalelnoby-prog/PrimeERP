from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.services.base_service import BaseService
from app.modules.roles.models import Role
from app.modules.roles.repositories.permission_repository import (
    permission_repository,
)
from app.modules.roles.repositories.role_repository import (
    RoleRepository,
    role_repository,
)


class RoleService(BaseService[RoleRepository]):
    def __init__(
        self,
        *,
        db: Session | None = None,
        current_user: Any | None = None,
        current_tenant: Any | None = None,
        repository: RoleRepository = role_repository,
    ) -> None:
        super().__init__(
            repository=repository,
            db=db,
            current_user=current_user,
            current_tenant=current_tenant,
        )

    def list_roles(self) -> list[Role]:
        db = self.require_db()
        repository = self.require_repository()

        roles = repository.list_with_permissions(db)

        for role in roles:
            role.users_count = len(role.users)

        return roles

    def get_by_id(
        self,
        role_id: int,
    ) -> Role | None:
        db = self.require_db()
        repository = self.require_repository()

        role = repository.get_with_permissions(
            db,
            role_id,
        )

        if role is not None:
            role.users_count = len(role.users)

        return role

    def create_role(
        self,
        *,
        name: str,
        description: str | None = None,
        permission_ids: list[int] | None = None,
        is_active: bool = True,
    ) -> Role:
        db = self.require_db()
        repository = self.require_repository()

        normalized_name = name.strip()

        if not normalized_name:
            raise ValueError(
                "Role name is required."
            )

        if repository.exists_by_name(
            db,
            normalized_name,
        ):
            raise ValueError(
                "Role name already exists."
            )

        permissions = self._get_permissions(
            permission_ids or []
        )

        with self.uow as uow:
            role = repository.create(
                db,
                data={
                    "name": normalized_name,
                    "description": (
                        description.strip()
                        if description
                        else None
                    ),
                    "is_active": is_active,
                },
            )

            role.permissions = permissions
            uow.commit()

        return self._reload_role(role.id)

    def update_role(
        self,
        role_id: int,
        *,
        name: str | None = None,
        description: str | None = None,
        is_active: bool | None = None,
        permission_ids: list[int] | None = None,
    ) -> Role:
        db = self.require_db()
        repository = self.require_repository()

        role = repository.get_with_permissions(
            db,
            role_id,
        )

        if role is None:
            raise LookupError(
                "Role was not found."
            )

        update_data: dict[str, Any] = {}

        if name is not None:
            normalized_name = name.strip()

            if not normalized_name:
                raise ValueError(
                    "Role name is required."
                )

            if repository.exists_by_name(
                db,
                normalized_name,
                exclude_role_id=role_id,
            ):
                raise ValueError(
                    "Role name already exists."
                )

            update_data["name"] = normalized_name

        if description is not None:
            update_data["description"] = (
                description.strip() or None
            )

        if is_active is not None:
            update_data["is_active"] = is_active

        permissions = None

        if permission_ids is not None:
            permissions = self._get_permissions(
                permission_ids
            )

        with self.uow as uow:
            if update_data:
                for field, value in update_data.items():
                    setattr(role, field, value)

            if permissions is not None:
                role.permissions = permissions

            uow.commit()

        return self._reload_role(role_id)

    def change_status(
        self,
        role_id: int,
        *,
        is_active: bool,
    ) -> Role:
        return self.update_role(
            role_id,
            is_active=is_active,
        )

    def update_permissions(
        self,
        role_id: int,
        *,
        permission_ids: list[int],
    ) -> Role:
        return self.update_role(
            role_id,
            permission_ids=permission_ids,
        )

    def delete_role(
        self,
        role_id: int,
    ) -> None:
        db = self.require_db()
        repository = self.require_repository()

        role = repository.get_with_permissions(
            db,
            role_id,
        )

        if role is None:
            raise LookupError(
                "Role was not found."
            )

        if role.users:
            raise ValueError(
                "Role cannot be deleted because it is assigned "
                "to one or more users."
            )

        with self.uow as uow:
            db.delete(role)
            uow.commit()

    def _get_permissions(
        self,
        permission_ids: list[int],
    ) -> list:
        db = self.require_db()

        unique_ids = list(
            dict.fromkeys(permission_ids)
        )

        permissions = permission_repository.get_by_ids(
            db,
            unique_ids,
        )

        if len(permissions) != len(unique_ids):
            found_ids = {
                permission.id
                for permission in permissions
            }

            missing_ids = sorted(
                set(unique_ids) - found_ids
            )

            raise ValueError(
                f"Permissions were not found: {missing_ids}"
            )

        return permissions

    def _reload_role(
        self,
        role_id: int,
    ) -> Role:
        db = self.require_db()
        repository = self.require_repository()

        role = repository.get_with_permissions(
            db,
            role_id,
        )

        if role is None:
            raise RuntimeError(
                "Role could not be reloaded."
            )

        role.users_count = len(role.users)

        return role


role_service = RoleService()