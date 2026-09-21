from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.audit.models import AuditEvent
from app.modules.accounting.chart_of_accounts.models import AccountCombination, NaturalAccount
from app.modules.accounting.journals.models.journal_entry import JournalEntry
from app.modules.accounting.journals.models.journal_entry_line import JournalEntryLine
from app.modules.companies.models import Company
from app.modules.branches.models import Branch
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tenant_id = current_user.tenant_id
    if tenant_id is None:
        return {
            "tenant": None,
            "users": {"total": 0, "active": 0},
            "companies": {"total": 0, "active": 0},
            "branches": {"total": 0, "active": 0},
            "revenue_overview": [],
            "recent_activities": [],
        }

    users_total = db.scalar(select(func.count(User.id)).where(User.tenant_id == tenant_id, User.is_deleted.is_(False))) or 0
    users_active = db.scalar(select(func.count(User.id)).where(User.tenant_id == tenant_id, User.is_deleted.is_(False), User.is_active.is_(True))) or 0
    companies_total = db.scalar(select(func.count(Company.id)).where(Company.tenant_id == tenant_id)) or 0
    companies_active = db.scalar(select(func.count(Company.id)).where(Company.tenant_id == tenant_id, Company.is_active.is_(True))) or 0
    branches_total = db.scalar(select(func.count(Branch.id)).where(Branch.tenant_id == tenant_id)) or 0
    branches_active = db.scalar(select(func.count(Branch.id)).where(Branch.tenant_id == tenant_id, Branch.is_active.is_(True))) or 0

    now = datetime.now(timezone.utc)
    start = (now.replace(day=1) - timedelta(days=185)).replace(day=1)
    month_expr = func.date_trunc("month", JournalEntry.entry_date)
    revenue_expr = func.coalesce(func.sum(JournalEntryLine.base_credit - JournalEntryLine.base_debit), 0)
    expense_expr = func.coalesce(func.sum(JournalEntryLine.base_debit - JournalEntryLine.base_credit), 0)

    rows = db.execute(
        select(
            month_expr.label("month"),
            func.coalesce(
                func.sum(
                    func.case(
                        (NaturalAccount.account_category.ilike("%revenue%"), JournalEntryLine.base_credit - JournalEntryLine.base_debit),
                        else_=0,
                    )
                ), 0
            ).label("revenue"),
            func.coalesce(
                func.sum(
                    func.case(
                        (NaturalAccount.account_category.ilike("%expense%"), JournalEntryLine.base_debit - JournalEntryLine.base_credit),
                        else_=0,
                    )
                ), 0
            ).label("expenses"),
        )
        .join(JournalEntryLine, JournalEntryLine.entry_id == JournalEntry.id)
        .join(AccountCombination, AccountCombination.id == JournalEntryLine.account_combination_id)
        .join(NaturalAccount, NaturalAccount.id == AccountCombination.natural_account_id)
        .where(
            JournalEntry.tenant_id == tenant_id,
            JournalEntry.status == "posted",
            JournalEntry.entry_date >= start.date(),
            NaturalAccount.financial_statement == "profit_and_loss",
        )
        .group_by(month_expr)
        .order_by(month_expr)
    ).all()

    revenue_overview = [
        {"month": row.month.strftime("%b %Y"), "revenue": float(row.revenue or 0), "expenses": float(row.expenses or 0)}
        for row in rows
    ]

    activities = db.scalars(
        select(AuditEvent)
        .where(AuditEvent.tenant_id == tenant_id)
        .order_by(AuditEvent.created_at.desc())
        .limit(8)
    ).all()

    recent_activities = [
        {
            "id": row.id,
            "title": f"{row.entity_type}: {row.action}",
            "description": f"Entity {row.entity_id}" if row.entity_id else "System activity",
            "time": row.created_at.isoformat() if row.created_at else "",
            "status": (
                "danger" if any(x in row.action.lower() for x in ("fail", "error", "delete"))
                else "success" if any(x in row.action.lower() for x in ("create", "post", "approve", "login"))
                else "info"
            ),
        }
        for row in activities
    ]

    tenant = current_user.tenant
    return {
        "tenant": {
            "id": tenant.id if tenant else tenant_id,
            "name": tenant.name if tenant else None,
            "slug": tenant.slug if tenant else None,
        },
        "users": {"total": users_total, "active": users_active},
        "companies": {"total": companies_total, "active": companies_active},
        "branches": {"total": branches_total, "active": branches_active},
        "revenue_overview": revenue_overview,
        "recent_activities": recent_activities,
    }
