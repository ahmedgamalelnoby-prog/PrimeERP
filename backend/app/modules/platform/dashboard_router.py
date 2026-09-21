from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.companies.models import Company
from app.modules.branches.models import Branch
from app.modules.commerce.models import SalesDocument
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User

router = APIRouter(prefix="/platform/dashboard", tags=["platform-dashboard"])


@router.get("/summary")
def dashboard_summary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    """Return tenant-scoped live KPIs for the main dashboard."""
    tenant_id = current_user.tenant_id
    if tenant_id is None:
        return {"companies": 0, "branches": 0, "users": 0, "customers": 0, "revenue_current_month": 0, "revenue_previous_month": 0}

    companies = db.scalar(select(func.count(Company.id)).where(Company.tenant_id == tenant_id, Company.is_active.is_(True))) or 0
    branches = db.scalar(select(func.count(Branch.id)).where(Branch.tenant_id == tenant_id, Branch.is_active.is_(True))) or 0
    users = db.scalar(select(func.count(User.id)).where(User.tenant_id == tenant_id, User.is_active.is_(True), User.is_deleted.is_(False))) or 0

    first_of_month = date.today().replace(day=1)
    current_revenue = db.scalar(
        select(func.coalesce(func.sum(SalesDocument.total), 0))
        .join(Company, Company.id == SalesDocument.company_id)
        .where(Company.tenant_id == tenant_id, SalesDocument.document_type == "invoice", SalesDocument.status == "posted", SalesDocument.document_date >= first_of_month)
    ) or 0

    previous_month_start = (first_of_month.replace(day=1) - __import__("datetime").timedelta(days=1)).replace(day=1)
    previous_revenue = db.scalar(
        select(func.coalesce(func.sum(SalesDocument.total), 0))
        .join(Company, Company.id == SalesDocument.company_id)
        .where(Company.tenant_id == tenant_id, SalesDocument.document_type == "invoice", SalesDocument.status == "posted", SalesDocument.document_date >= previous_month_start, SalesDocument.document_date < first_of_month)
    ) or 0

    customers = db.scalar(
        select(func.count(func.distinct(SalesDocument.partner_id)))
        .join(Company, Company.id == SalesDocument.company_id)
        .where(Company.tenant_id == tenant_id)
    ) or 0

    return {
        "companies": int(companies),
        "branches": int(branches),
        "users": int(users),
        "customers": int(customers),
        "revenue_current_month": float(current_revenue),
        "revenue_previous_month": float(previous_revenue),
    }
