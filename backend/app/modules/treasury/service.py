from sqlalchemy import select
from sqlalchemy.orm import Session
from app.modules.treasury.models import PaymentMethod, TreasuryPayment


class TreasuryService:
    def list_methods(self, db: Session, company_id: int):
        return list(db.scalars(select(PaymentMethod).where(PaymentMethod.company_id == company_id).order_by(PaymentMethod.id)).all())

    def create_method(self, db: Session, payload):
        if not payload.is_incoming and not payload.is_outgoing:
            raise ValueError("Payment method must support receipt, payment, or both")
        duplicate = db.scalar(select(PaymentMethod).where(PaymentMethod.company_id == payload.company_id, PaymentMethod.code == payload.code.strip()))
        if duplicate:
            raise ValueError("Payment method code already exists for this company")
        method = PaymentMethod(company_id=payload.company_id, code=payload.code.strip(), name=payload.name.strip(), method_type=payload.method_type.strip(), is_incoming=int(payload.is_incoming), is_outgoing=int(payload.is_outgoing), is_active=1)
        db.add(method); db.flush(); return method

    def list_payments(self, db: Session, company_id: int, party_type: str | None = None, direction: str | None = None):
        stmt = select(TreasuryPayment).where(TreasuryPayment.company_id == company_id)
        if party_type: stmt = stmt.where(TreasuryPayment.party_type == party_type)
        if direction: stmt = stmt.where(TreasuryPayment.direction == direction)
        return list(db.scalars(stmt.order_by(TreasuryPayment.id.desc())).all())

    def create_payment(self, db: Session, payload):
        if payload.party_type not in {"customer", "supplier", "other"}:
            raise ValueError("Invalid party type")
        if payload.direction not in {"receipt", "payment"}:
            raise ValueError("Direction must be receipt or payment")
        method = db.scalar(select(PaymentMethod).where(PaymentMethod.id == payload.payment_method_id, PaymentMethod.company_id == payload.company_id, PaymentMethod.is_active == 1))
        if method is None: raise ValueError("Payment method not found for this company")
        if payload.direction == "receipt" and not method.is_incoming: raise ValueError("Payment method does not support receipts")
        if payload.direction == "payment" and not method.is_outgoing: raise ValueError("Payment method does not support payments")
        payment = TreasuryPayment(**payload.model_dump(), currency_code=payload.currency_code.upper(), status="posted")
        db.add(payment); db.flush(); return payment

    def reverse_payment(self, db: Session, company_id: int, payment_id: int, notes: str | None = None):
        original = db.scalar(select(TreasuryPayment).where(TreasuryPayment.id == payment_id, TreasuryPayment.company_id == company_id).with_for_update())
        if original is None: raise ValueError("Payment not found")
        if original.status != "posted": raise ValueError("Only posted payments can be reversed")
        if original.reversed_payment_id is not None: raise ValueError("Payment has already been reversed")
        reversal = TreasuryPayment(company_id=original.company_id, branch_id=original.branch_id, payment_method_id=original.payment_method_id, party_type=original.party_type, party_id=original.party_id, direction="payment" if original.direction == "receipt" else "receipt", payment_date=original.payment_date, amount=original.amount, currency_code=original.currency_code, reference=original.reference, source_module="treasury", source_entity="payment_reversal", source_id=str(original.id), status="posted", notes=notes or f"Reversal of payment {original.id}")
        db.add(reversal); db.flush()
        original.status = "reversed"; original.reversed_payment_id = reversal.id
        db.flush(); return reversal


treasury_service = TreasuryService()
