from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from app.modules.inventory.items.models import InventoryItem
from app.modules.platform.customers.models import Customer
from app.modules.sales.quotations.models import SalesQuotation, SalesQuotationLine

class SalesQuotationService:
    def list(self, db: Session, company_id: int):
        return list(db.scalars(select(SalesQuotation).options(selectinload(SalesQuotation.lines)).where(SalesQuotation.company_id == company_id).order_by(SalesQuotation.id.desc())).unique().all())

    def get(self, db: Session, company_id: int, quotation_id: int):
        return db.scalar(select(SalesQuotation).options(selectinload(SalesQuotation.lines)).where(SalesQuotation.company_id == company_id, SalesQuotation.id == quotation_id))

    def create(self, db: Session, payload):
        customer = db.scalar(select(Customer).where(Customer.id == payload.customer_id, Customer.company_id == payload.company_id, Customer.is_active.is_(True)))
        if customer is None:
            raise ValueError("Customer does not belong to the company or is inactive")
        if db.scalar(select(SalesQuotation).where(SalesQuotation.company_id == payload.company_id, SalesQuotation.quotation_number == payload.quotation_number)):
            raise ValueError("Quotation number already exists for this company")
        ids = {line.item_id for line in payload.lines}
        items = list(db.scalars(select(InventoryItem).where(InventoryItem.company_id == payload.company_id, InventoryItem.id.in_(ids), InventoryItem.is_active.is_(True))).all())
        if len(items) != len(ids):
            raise ValueError("One or more items do not belong to the company or are inactive")
        quotation = SalesQuotation(company_id=payload.company_id, customer_id=payload.customer_id, quotation_number=payload.quotation_number, quotation_date=payload.quotation_date, valid_until=payload.valid_until, notes=payload.notes, total_amount=Decimal("0"))
        db.add(quotation); db.flush()
        total = Decimal("0")
        for line in payload.lines:
            gross = line.quantity * line.unit_price
            if line.discount_amount > gross:
                raise ValueError("Discount cannot exceed the line gross amount")
            line_total = gross - line.discount_amount
            db.add(SalesQuotationLine(quotation_id=quotation.id, item_id=line.item_id, quantity=line.quantity, unit_price=line.unit_price, discount_amount=line.discount_amount, line_total=line_total))
            total += line_total
        quotation.total_amount = total
        db.flush()
        return quotation

    def transition(self, db: Session, company_id: int, quotation_id: int, target: str):
        quotation = db.scalar(select(SalesQuotation).where(SalesQuotation.company_id == company_id, SalesQuotation.id == quotation_id).with_for_update())
        if quotation is None:
            raise ValueError("Quotation not found")
        allowed = {"draft": {"sent", "cancelled"}, "sent": {"accepted", "rejected", "expired", "cancelled"}}
        if target not in allowed.get(quotation.status, set()):
            raise ValueError(f"Invalid quotation transition: {quotation.status} -> {target}")
        quotation.status = target
        db.flush()
        return quotation

sales_quotation_service = SalesQuotationService()
