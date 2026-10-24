from datetime import date
from typing import Optional

from sqlalchemy.orm import (
    Session,
    joinedload,
)

from app.modules.accounting.fiscal_years.models import (
    AccountingPeriod,
    FiscalYear,
)


class FiscalYearRepository:
    def get_by_id(
        self,
        db: Session,
        fiscal_year_id: int,
        tenant_id: int,
        for_update: bool = False,
    ) -> Optional[FiscalYear]:
        query = (
            db.query(FiscalYear)
            .options(
                joinedload(
                    FiscalYear.periods
                )
            )
            .filter(
                FiscalYear.id
                == fiscal_year_id,
                FiscalYear.tenant_id
                == tenant_id,
            )
        )

        if for_update:
            query = query.with_for_update()

        return query.first()

    def list_by_company(
        self,
        db: Session,
        tenant_id: int,
        company_id: int,
    ) -> list[FiscalYear]:
        return (
            db.query(FiscalYear)
            .options(
                joinedload(
                    FiscalYear.periods
                )
            )
            .filter(
                FiscalYear.tenant_id
                == tenant_id,
                FiscalYear.company_id
                == company_id,
            )
            .order_by(
                FiscalYear.start_date.desc()
            )
            .all()
        )

    def find_overlapping_year(
        self,
        db: Session,
        tenant_id: int,
        company_id: int,
        start_date: date,
        end_date: date,
        exclude_id: Optional[int] = None,
    ) -> Optional[FiscalYear]:
        query = (
            db.query(FiscalYear)
            .filter(
                FiscalYear.tenant_id
                == tenant_id,
                FiscalYear.company_id
                == company_id,
                FiscalYear.start_date
                <= end_date,
                FiscalYear.end_date
                >= start_date,
            )
        )

        if exclude_id is not None:
            query = query.filter(
                FiscalYear.id != exclude_id
            )

        return query.first()

    def get_period_by_id(
        self,
        db: Session,
        period_id: int,
        tenant_id: int,
        for_update: bool = False,
    ) -> Optional[AccountingPeriod]:
        query = (
            db.query(AccountingPeriod)
            .filter(
                AccountingPeriod.id == period_id,
                AccountingPeriod.tenant_id
                == tenant_id,
            )
        )

        if for_update:
            query = query.with_for_update()

        return query.first()

    def get_period_for_date(
        self,
        db: Session,
        tenant_id: int,
        company_id: int,
        posting_date: date,
        require_open: bool = True,
    ) -> Optional[AccountingPeriod]:
        query = (
            db.query(AccountingPeriod)
            .filter(
                AccountingPeriod.tenant_id
                == tenant_id,
                AccountingPeriod.company_id
                == company_id,
                AccountingPeriod.start_date
                <= posting_date,
                AccountingPeriod.end_date
                >= posting_date,
            )
        )
        if require_open:
            query = query.filter(
                AccountingPeriod.status == "open",
                AccountingPeriod.allow_posting.is_(True),
            )
        return query.order_by(
            AccountingPeriod.start_date.desc(),
            AccountingPeriod.end_date.desc(),
            AccountingPeriod.id.desc(),
        ).first()


fiscal_year_repository = (
    FiscalYearRepository()
)