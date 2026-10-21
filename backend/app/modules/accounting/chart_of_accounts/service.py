"""Application services for Chart of Accounts."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import AccountingCostCenter, AccountingDepartment, NaturalAccount


class ChartOfAccountsService:
    """Transaction-safe query helpers for chart dimensions."""

    @staticmethod
    def list_departments(db: Session, company_id: int, *, active_only: bool = True):
        stmt = select(AccountingDepartment).where(AccountingDepartment.company_id == company_id)
        if active_only:
            stmt = stmt.where(AccountingDepartment.is_active.is_(True))
        return db.scalars(stmt.order_by(AccountingDepartment.code)).all()

    @staticmethod
    def list_cost_centers(db: Session, company_id: int, *, active_only: bool = True):
        stmt = select(AccountingCostCenter).where(AccountingCostCenter.company_id == company_id)
        if active_only:
            stmt = stmt.where(AccountingCostCenter.is_active.is_(True))
        return db.scalars(stmt.order_by(AccountingCostCenter.code)).all()

    @staticmethod
    def list_natural_accounts(db: Session, company_id: int, *, active_only: bool = True):
        stmt = select(NaturalAccount).where(NaturalAccount.company_id == company_id)
        if active_only:
            stmt = stmt.where(NaturalAccount.is_active.is_(True))
        return db.scalars(stmt.order_by(NaturalAccount.code)).all()

    @staticmethod
    def get_natural_account(db: Session, company_id: int, account_id: int) -> NaturalAccount | None:
        return db.scalar(
            select(NaturalAccount).where(
                NaturalAccount.id == account_id,
                NaturalAccount.company_id == company_id,
            )
        )
