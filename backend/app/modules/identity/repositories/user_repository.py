from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.database import BaseRepository
from app.modules.identity.models.user import User
from app.modules.saas.models import Tenant


class UserRepository(BaseRepository[User]):
    def __init__(self) -> None:
        super().__init__(User)

    def get_by_id(
        self,
        db: Session,
        user_id: int,
        *,
        tenant_id: int | None = None,
        include_deleted: bool = False,
        for_update: bool = False,
    ) -> User | None:
        query = select(User).where(
            User.id == user_id,
        )

        if tenant_id is not None:
            query = query.where(
                User.tenant_id == tenant_id,
            )

        if not include_deleted:
            query = query.where(
                User.is_deleted.is_(False),
            )

        if for_update:
            query = query.with_for_update()

        return db.execute(
            query
        ).scalar_one_or_none()

    def get_by_username(
        self,
        db: Session,
        username: str,
        *,
        tenant_id: int | None = None,
        include_deleted: bool = False,
    ) -> User | None:
        normalized_username = username.strip().lower()

        query = select(User).where(
            func.lower(User.username) == normalized_username,
        )

        if tenant_id is not None:
            query = query.where(
                User.tenant_id == tenant_id,
            )

        if not include_deleted:
            query = query.where(
                User.is_deleted.is_(False),
            )

        return db.execute(
            query
        ).scalar_one_or_none()

    def get_by_email(
        self,
        db: Session,
        email: str,
        *,
        tenant_id: int | None = None,
        include_deleted: bool = False,
    ) -> User | None:
        normalized_email = email.strip().lower()

        query = select(User).where(
            func.lower(User.email) == normalized_email,
        )

        if tenant_id is not None:
            query = query.where(
                User.tenant_id == tenant_id,
            )

        if not include_deleted:
            query = query.where(
                User.is_deleted.is_(False),
            )

        return db.execute(
            query
        ).scalar_one_or_none()

    def find_for_login(
        self,
        db: Session,
        login: str,
        *,
        tenant_slug: str | None = None,
        tenant_name: str | None = None,
    ) -> list[User]:
        """
        Returns up to two matching users.

        The service layer decides whether multiple matches
        represent a business conflict.
        """
        normalized_login = login.strip().lower()

        query = (
            select(User)
            .outerjoin(
                Tenant,
                Tenant.id == User.tenant_id,
            )
            .where(
                or_(
                    func.lower(User.email) == normalized_login,
                    func.lower(User.username) == normalized_login,
                ),
                User.is_deleted.is_(False),
            )
        )

        if tenant_slug:
            query = query.where(
                func.lower(Tenant.slug) == tenant_slug.strip().lower()
            )
        if tenant_name:
            query = query.where(
                or_(
                    User.is_platform_admin.is_(True),
                    func.lower(Tenant.name) == tenant_name.strip().lower(),
                )
            )

        query = query.limit(2)

        return list(
            db.execute(query).scalars().all()
        )

    def list_users(
        self,
        db: Session,
        *,
        tenant_id: int | None,
        search: str | None = None,
        is_active: bool | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[User]:
        query = select(User).where(
            User.is_deleted.is_(False),
        )

        if tenant_id is not None:
            query = query.where(
                User.tenant_id == tenant_id,
            )

        if search:
            search_value = f"%{search.strip()}%"

            query = query.where(
                or_(
                    User.username.ilike(search_value),
                    User.email.ilike(search_value),
                    User.full_name.ilike(search_value),
                    User.phone.ilike(search_value),
                )
            )

        if is_active is not None:
            query = query.where(
                User.is_active == is_active,
            )

        query = (
            query
            .order_by(User.id.desc())
            .offset(skip)
            .limit(limit)
        )

        return list(
            db.execute(query).scalars().all()
        )

    def count_users(
        self,
        db: Session,
        *,
        tenant_id: int | None,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> int:
        query = select(func.count(User.id)).where(
            User.is_deleted.is_(False),
        )

        if tenant_id is not None:
            query = query.where(
                User.tenant_id == tenant_id,
            )

        if search:
            value = f"%{search.strip()}%"

            query = query.where(
                or_(
                    User.username.ilike(value),
                    User.email.ilike(value),
                    User.full_name.ilike(value),
                    User.phone.ilike(value),
                )
            )

        if is_active is not None:
            query = query.where(
                User.is_active == is_active,
            )

        return db.execute(query).scalar_one()
user_repository = UserRepository()