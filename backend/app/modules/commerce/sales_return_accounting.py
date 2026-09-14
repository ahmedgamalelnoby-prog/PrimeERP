from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.commerce.accounting_service import commerce_accounting_service
from app.modules.commerce.accounting_models import CommerceAccountingSettings
from app.modules.commerce.models import SalesLine
from app.modules.commerce.sales_return_models import SalesReturnAllocation


def post_sales_return_cogs(db: Session, document, user_id: int):
    settings = commerce_accounting_service._settings(db, document.company_id)
    allocations = list(db.scalars(select(SalesReturnAllocation).join(SalesLine, SalesLine.id == SalesReturnAllocation.credit_note_line_id).where(SalesReturnAllocation.company_id == document.company_id, SalesLine.document_id == document.id)))
    total = sum((Decimal(row.quantity) * Decimal(row.unit_cost) for row in allocations), Decimal("0"))
    if total <= 0:
        return None
    return commerce_accounting_service._post(
        db,
        company_id=document.company_id,
        user_id=user_id,
        entry_date=document.document_date,
        journal_id=settings.sales_journal_id,
        entry_number=f"RCN-COGS-{document.id}",
        description=f"COGS reversal for sales return {document.number}",
        lines=[
            {"account_combination_id": settings.inventory_account_id, "debit": total, "credit": 0, "description": f"Inventory returned {document.number}"},
            {"account_combination_id": settings.cogs_account_id, "debit": 0, "credit": total, "description": f"COGS reversal {document.number}"},
        ],
        source_entity="sales_return_cogs",
        source_id=document.id,
    )
