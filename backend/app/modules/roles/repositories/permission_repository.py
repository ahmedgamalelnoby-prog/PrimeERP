from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database.base_repository import BaseRepository
from app.modules.roles.models import Permission
from app.shared.query import QueryOptions


class PermissionRepository(BaseRepository[Permission]):
    def __init__(self) -> None:
        super().__init__(
            model=Permission,
            query_options=QueryOptions(
                filterable_fields={
                    "id",
                    "resource",
                    "action",
                    "is_active",
                },
                searchable_fields={
                    "name",
                    "description",
                    "resource",
                    "action",
                },
                sortable_fields={
                    "id",
                    "name",
                    "resource",
                    "action",
                    "created_at",
                },
            ),
        )

    def exists_by_name(
        self,
        db: Session,
        name: str,
    ) -> bool:
        return self.exists(
            db,
            name=name,
        )

    def exists_by_resource_action(
        self,
        db: Session,
        *,
        resource: str,
        action: str,
    ) -> bool:
        return self.exists(
            db,
            resource=resource,
            action=action,
        )

    def get_by_ids(
        self,
        db: Session,
        permission_ids: list[int],
    ) -> list[Permission]:
        if not permission_ids:
            return []

        unique_ids = list(
            dict.fromkeys(permission_ids)
        )

        result = db.execute(
            select(Permission).where(
                Permission.id.in_(unique_ids)
            )
        )

        return list(
            result.scalars().all()
        )


permission_repository = PermissionRepository()