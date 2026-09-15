from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.commerce.models import CommercePayment, PurchaseDocument, SalesDocument
from app.modules.jurisdiction.models import TaxSnapshot
from app.modules.jurisdiction.tax_posting_guard import validate_payment_wht


PAYMENT_METHODS = {"cash", "bank_transfer", "card", "cheque", "wallet", "cod", "other"}


def _same_idempotent_payload(existing: CommercePayment, *, document_kind: str, document_id: int, amount: Decimal, wht_amount: Decimal, payment_date: date, method: str, reference: str | None) -> bool:
    return (
        existing.document_kind == document_kind
        and existing.document_id == document_id
        and Decimal(existing.amount) == Decimal(amount)
        and Decimal(existing.wht_amount or 0) == Decimal(wht_amount)
        and existing.payment_date == payment_date
        and existing.method == method
        and existing.reference == reference
    )


def post_payment(db: Session, *, company_id: int, document_kind: str, document_id: int, amount: Decimal, payment_date: date, method: str, wht_amount: Decimal = Decimal("0"), reference: str | None = None, notes: str | None = None, idempotency_key: str | None = None):
    if document_kind not in {"sale", "purchase"}:
        raise ValueError("Invalid document kind")
    if method not in PAYMENT_METHODS:
        raise ValueError("Invalid payment method")
    if amount <= 0:
        raise ValueError("Payment amount must be positive")
    if wht_amount < 0 or wht_amount > amount:
        raise ValueError("Invalid withholding amount")

    model = SalesDocument if document_kind == "sale" else PurchaseDocument
    document = db.scalar(select(model).where(model.id == document_id, model.company_id == company_id).with_for_update())
    if document is None:
        raise ValueError("Document not found")

    snapshot = db.scalar(select(TaxSnapshot).where(
        TaxSnapshot.company_id == company_id,
        TaxSnapshot.document_kind == document_kind,
        TaxSnapshot.document_id == document_id,
    ).with_for_update())
    if snapshot is None:
        raise ValueError("Tax snapshot is required before posting payment")

    if idempotency_key:
        existing = db.scalar(select(CommercePayment).where(
            CommercePayment.company_id == company_id,
            CommercePayment.idempotency_key == idempotency_key,
        ).with_for_update())
        if existing:
            if not _same_idempotent_payload(existing, document_kind=document_kind, document_id=document_id, amount=amount, wht_amount=wht_amount, payment_date=payment_date, method=method, reference=reference):
                raise ValueError("Idempotency key has already been used with a different payment payload")
            if existing.status != "posted":
                raise ValueError("The idempotent payment is no longer posted")
            return document, existing

    balance = Decimal(document.total or 0) - Decimal(document.paid_total or 0)
    if amount > balance:
        raise ValueError("Payment exceeds outstanding balance")

    candidate = CommercePayment(
        company_id=company_id,
        document_kind=document_kind,
        document_id=document_id,
        payment_date=payment_date,
        amount=amount,
        wht_amount=wht_amount,
        method=method,
        reference=reference,
        notes=notes,
        idempotency_key=idempotency_key,
        status="posted",
    )
    validate_payment_wht(candidate, snapshot)

    if idempotency_key:
        # The pre-check above avoids the normal duplicate path. The nested
        # transaction closes the remaining race where another transaction
        # inserts the same company/key between the SELECT and INSERT.
        try:
            with db.begin_nested():
                db.add(candidate)
                document.paid_total = Decimal(document.paid_total or 0) + amount
                db.flush()
        except IntegrityError as exc:
            existing = db.scalar(select(CommercePayment).where(
                CommercePayment.company_id == company_id,
                CommercePayment.idempotency_key == idempotency_key,
            ).with_for_update())
            if existing is None:
                raise exc
            if not _same_idempotent_payload(existing, document_kind=document_kind, document_id=document_id, amount=amount, wht_amount=wht_amount, payment_date=payment_date, method=method, reference=reference):
                raise ValueError("Idempotency key has already been used with a different payment payload")
            if existing.status != "posted":
                raise ValueError("The idempotent payment is no longer posted")
            return document, existing
        return document, candidate

    db.add(candidate)
    document.paid_total = Decimal(document.paid_total or 0) + amount
    db.flush()
    return document, candidate


def reverse_payment(db: Session, *, company_id: int, payment_id: int, reversal_date: date, notes: str | None = None):
    payment = db.scalar(select(CommercePayment).where(CommercePayment.id == payment_id, CommercePayment.company_id == company_id).with_for_update())
    if payment is None:
        raise ValueError("Payment not found")
    if payment.status != "posted" or payment.reversed_of_id is not None:
        raise ValueError("Only an original posted payment can be reversed")
    model = SalesDocument if payment.document_kind == "sale" else PurchaseDocument
    document = db.scalar(select(model).where(model.id == payment.document_id, model.company_id == company_id).with_for_update())
    if document is None:
        raise ValueError("Document not found")
    if Decimal(document.paid_total or 0) < Decimal(payment.amount):
        raise ValueError("Document paid total is inconsistent")
    payment.status = "reversed"
    payment.reversed_at = reversal_date
    reversal = CommercePayment(company_id=company_id, document_kind=payment.document_kind, document_id=payment.document_id, payment_date=reversal_date, amount=payment.amount, wht_amount=payment.wht_amount, method=payment.method, reference=f"REV-{payment.id}", notes=notes or f"Reversal of payment {payment.id}", status="reversed", reversed_of_id=payment.id, reversed_at=reversal_date)
    db.add(reversal)
    document.paid_total = Decimal(document.paid_total or 0) - Decimal(payment.amount)
    db.flush()
    return document, payment, reversal
