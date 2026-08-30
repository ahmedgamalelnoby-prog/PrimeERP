from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.database.base_repository import BaseRepository
from app.modules.saas.models import Tenant


class TenantRepository(BaseRepository[Tenant]):
    def __init__(self) -> None:
        super().__init__(model=Tenant)

    def get_by_slug(
        self,
        db: Session,
        slug: str,
        *,
        for_update: bool = False,
    ) -> Tenant | None:
        statement = select(Tenant).where(
            Tenant.slug == slug
        )

        if for_update:
            statement = statement.with_for_update()

        return db.execute(statement).scalar_one_or_none()

    def slug_exists(
        self,
        db: Session,
        slug: str,
        *,
        exclude_id: int | None = None,
    ) -> bool:
        statement = select(Tenant.id).where(
            Tenant.slug == slug
        )

        if exclude_id is not None:
            statement = statement.where(
                Tenant.id != exclude_id
            )

        return db.execute(statement).first() is not None

    def list_tenants(
        self,
        db: Session,
        *,
        search: str | None = None,
        status: str | None = None,
        is_active: bool | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Tenant], int]:
        filters = []

        if search:
            search_value = f"%{search.strip()}%"

            filters.append(
                or_(
                    Tenant.name.ilike(search_value),
                    Tenant.slug.ilike(search_value),
                    Tenant.owner_name.ilike(search_value),
                    Tenant.email.ilike(search_value),
                )
            )

        if status is not None:
            filters.append(Tenant.status == status)

        if is_active is not None:
            filters.append(Tenant.is_active == is_active)

        total_statement = select(
            func.count(Tenant.id)
        ).where(*filters)

        total = int(
            db.execute(total_statement).scalar_one()
        )

        statement = (
            select(Tenant)
            .where(*filters)
            .order_by(
                Tenant.created_at.desc(),
                Tenant.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        items = list(
            db.execute(statement).scalars().all()
        )

        return items, total