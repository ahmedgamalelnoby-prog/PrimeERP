from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database.base_repository import BaseRepository
from app.modules.platform.plans.models import Plan


class PlanRepository(BaseRepository[Plan]):

    def __init__(self) -> None:
        super().__init__(
            model=Plan,
        )

    def get_by_id(
        self,
        db: Session,
        plan_id: int,
        *,
        for_update: bool = False,
    ) -> Optional[Plan]:
        query = select(Plan).where(
            Plan.id == plan_id,
            Plan.is_deleted.is_(False),
        )

        if for_update:
            query = query.with_for_update()

        return db.execute(
            query
        ).scalar_one_or_none()

    def get_by_code(
        self,
        db: Session,
        code: str,
        version: int = 1,
    ) -> Optional[Plan]:
        query = select(Plan).where(
            Plan.code == code,
            Plan.version == version,
            Plan.is_deleted.is_(False),
        )

        return db.execute(
            query
        ).scalar_one_or_none()

    def get_default(
        self,
        db: Session,
    ) -> Optional[Plan]:
        query = select(Plan).where(
            Plan.is_default.is_(True),
            Plan.is_deleted.is_(False),
        )

        return db.execute(
            query
        ).scalar_one_or_none()

    def get_all(
        self,
        db: Session,
    ) -> list[Plan]:
        query = (
            select(Plan)
            .where(
                Plan.is_deleted.is_(False),
            )
            .order_by(
                Plan.sort_order.asc(),
                Plan.name.asc(),
            )
        )

        return list(
            db.execute(
                query
            ).scalars().all()
        )