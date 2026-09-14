from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from fastapi import HTTPException, status


TAX_SCALE = Decimal("0.01")
INDIRECT_TAX_TYPES = {"vat", "gst", "sales_tax"}


def _money(value: Any) -> Decimal:
    return Decimal(str(value or 0)).quantize(TAX_SCALE, rounding=ROUND_HALF_UP)


def _document_net_base(document: Any) -> Decimal:
    """Return the untaxed net base; line_total includes tax in PrimeERP."""
    subtotal = getattr(document, "subtotal", None)
    if subtotal is not None:
        return _money(subtotal)
    total = Decimal("0")
    for line in getattr(document, "lines", []):
        qty = Decimal(str(getattr(line, "quantity", 0) or 0))
        price = Decimal(str(getattr(line, "unit_price", 0) or 0))
        discount = Decimal(str(getattr(line, "discount_percent", 0) or 0))
        total += qty * price * (Decimal("100") - discount) / Decimal("100")
    return _money(total)


def validate_snapshot_tax(document: Any, snapshot: Any) -> None:
    """Validate document indirect tax against the immutable jurisdiction snapshot."""
    if snapshot.company_id != document.company_id or snapshot.document_id != document.id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tax snapshot does not belong to this document")
    if snapshot.transaction_date != document.document_date:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tax snapshot date does not match the document date")

    rules = snapshot.rules or []
    applicable = [r for r in rules if r.get("tax_type") in INDIRECT_TAX_TYPES]
    base = _document_net_base(document)
    expected = Decimal("0")
    for rule in applicable:
        rate = _money(rule.get("rate"))
        if rate < 0:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Invalid negative tax rate in snapshot rule {rule.get('code')}")
        expected += base * rate / Decimal("100")

    expected = _money(expected)
    actual = _money(getattr(document, "tax_total", 0))
    if applicable and actual != expected:
        codes = ", ".join(str(r.get("code")) for r in applicable)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Tax total {actual} does not match jurisdiction snapshot {expected}; rules: {codes}")
    if not applicable and actual != 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Document has tax but the jurisdiction snapshot contains no applicable VAT/GST/sales-tax rule")


def validate_payment_wht(payment: Any, snapshot: Any) -> None:
    """Validate settlement WHT against the immutable document snapshot.

    WHT is calculated on the document's untaxed subtotal and allocated to a
    partial payment in proportion to the gross amount settled. This mirrors
    PrimeERP's payment allocation rule and prevents a later Tax Master change
    from altering a historical payment.
    """
    if snapshot.company_id != payment.company_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tax snapshot does not belong to the payment company")
    gross = _money(payment.amount)
    wht = _money(payment.wht_amount)
    if wht < 0 or wht > gross:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Withholding tax must be between zero and the gross payment")

    rules = [r for r in (snapshot.rules or []) if r.get("tax_type") == "wht"]
    if not rules:
        if wht != 0:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Payment contains WHT but the jurisdiction snapshot contains no WHT rule")
        return

    subtotal = _money((snapshot.facts or {}).get("document_subtotal"))
    document_total = _money((snapshot.facts or {}).get("document_total"))
    if subtotal <= 0 or document_total <= 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tax snapshot is missing a valid taxable subtotal for WHT")

    document_wht_rate = sum((_money(r.get("rate")) for r in rules), Decimal("0"))
    document_wht = _money(subtotal * document_wht_rate / Decimal("100"))
    expected = _money(document_wht * gross / document_total)
    if wht != expected:
        codes = ", ".join(str(r.get("code")) for r in rules)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"WHT {wht} does not match jurisdiction snapshot {expected}; rules: {codes}")
