"""Persistence helpers for the canonical tax domain."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.accounting.models import TaxRate


def get_tax(db: Session, tax_id: int, company_id: int) -> TaxRate | None:
    return db.scalar(
        select(TaxRate).where(TaxRate.id == tax_id, TaxRate.company_id == company_id)
    )


def list_taxes(db: Session, company_id: int, *, active_only: bool = False) -> list[TaxRate]:
    stmt = select(TaxRate).where(TaxRate.company_id == company_id)
    if active_only:
        stmt = stmt.where(TaxRate.is_active.is_(True))
    return list(db.scalars(stmt.order_by(TaxRate.is_active.desc(), TaxRate.code)).all())


def get_tax_by_code(db: Session, company_id: int, code: str) -> TaxRate | None:
    return db.scalar(
        select(TaxRate).where(
            TaxRate.company_id == company_id,
            TaxRate.code == code.strip().upper(),
        )
    )
