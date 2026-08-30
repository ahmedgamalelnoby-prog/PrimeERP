from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.database.base_repository import BaseRepository
from app.modules.roles.models import Role
from app.shared.query import QueryOptions


class RoleRepository(BaseRepository[Role]):
    def __init__(self) -> None:
        super().__init__(
            model=Role,
            query_options=QueryOptions(
                filterable_fields={
                    "id",
                    "name",
                    "is_active",
                },
                searchable_fields={
                    "name",
                    "description",
                },
                sortable_fields={
                    "id",
                    "name",
                    "created_at",
                },
            ),
        )

    def get_with_permissions(
        self,
        db: Session,
        role_id: int,
    ) -> Role | None:
        return (
            db.execute(
                select(Role)
                .options(
                    selectinload(Role.permissions),
                    selectinload(Role.users),
                )
                .where(Role.id == role_id)
            )
            .scalar_one_or_none()
        )

    def list_with_permissions(
        self,
        db: Session,
    ) -> list[Role]:
        result = db.execute(
            select(Role)
            .options(
                selectinload(Role.permissions),
                selectinload(Role.users),
            )
            .order_by(Role.name.asc())
        )

        return list(
            result.scalars().unique().all()
        )

    def exists_by_name(
        self,
        db: Session,
        name: str,
        *,
        exclude_role_id: int | None = None,
    ) -> bool:
        statement = select(Role.id).where(
            func.lower(Role.name)
            == name.strip().lower()
        )

        if exclude_role_id is not None:
            statement = statement.where(
                Role.id != exclude_role_id
            )

        return (
            db.execute(statement).scalar_one_or_none()
            is not None
        )

    def count_users(
        self,
        db: Session,
        role_id: int,
    ) -> int:
        role = self.get_with_permissions(
            db,
            role_id,
        )

        if role is None:
            return 0

        return len(role.users)


role_repository = RoleRepository()