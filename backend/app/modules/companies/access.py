from sqlalchemy import select

from app.modules.companies.models import Company, user_company_access


def has_company_access(db, user_id: int, company_id: int, tenant_id: int) -> bool:
    return db.scalar(
        select(user_company_access.c.user_id)
        .join(Company, Company.id == user_company_access.c.company_id)
        .where(
            user_company_access.c.user_id == user_id,
            user_company_access.c.company_id == company_id,
            Company.tenant_id == tenant_id,
            Company.is_active.is_(True),
        )
    ) is not None


def assigned_company_ids(db, user_id: int, tenant_id: int) -> list[int]:
    return list(
        db.scalars(
            select(user_company_access.c.company_id)
            .join(Company, Company.id == user_company_access.c.company_id)
            .where(
                user_company_access.c.user_id == user_id,
                Company.tenant_id == tenant_id,
                Company.is_active.is_(True),
            )
            .order_by(user_company_access.c.is_default.desc(), Company.name, Company.id)
        ).all()
    )
