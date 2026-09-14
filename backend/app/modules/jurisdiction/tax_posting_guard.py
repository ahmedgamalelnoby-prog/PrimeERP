from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from fastapi import HTTPException, status


TAX_SCALE = Decimal("0.01")
INDIRECT_TAX_TYPES = {"vat", "gst", "sales_tax"}


def _money(value: Any) -> Decimal:
    return Decimal(str(value or 0)).quantize(TAX_SCALE, rounding=ROUND_HALF_UP)


def _line_base(line: Any) -> Decimal:
    if getattr(line, "line_total", None) is not None:
        return _money(line.line_total)
    qty = _money(getattr(line, "quantity", 0))
    price = _money(getattr(line, "unit_price", 0))
    discount = _money(getattr(line, "discount_percent", 0))
    return _money(qty * price * (Decimal("100") - discount) / Decimal("100"))


def validate_snapshot_tax(document: Any, snapshot: Any) -> None:
    """Validate document tax against the immutable jurisdiction rule snapshot.

    Only indirect transaction taxes (VAT/GST/sales tax) are compared with the
    document tax_total. WHT is withholding on settlement and is validated by
    the payment workflow, not treated as output/input tax on the invoice.
    """
    if snapshot.company_id != document.company_id or snapshot.document_id != document.id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tax snapshot does not belong to this document")
    if snapshot.transaction_date != document.document_date:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tax snapshot date does not match the document date")

    rules = snapshot.rules or []
    applicable = [r for r in rules if r.get("tax_type") in INDIRECT_TAX_TYPES]
    expected = Decimal("0")
    for rule in applicable:
        rate = _money(rule.get("rate"))
        if rate < 0:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Invalid negative tax rate in snapshot rule {rule.get('code')}")
        # The jurisdiction engine has already selected the applicable rules.
        # The rate is applied to the document's net taxable base. Line-level
        # exemptions/overrides are rejected unless their calculated tax agrees
        # with the jurisdiction total.
        base = sum((_line_base(line) for line in getattr(document, "lines", []) if _line_base(line) >= 0), Decimal("0"))
        expected += base * rate / Decimal("100")

    expected = _money(expected)
    actual = _money(getattr(document, "tax_total", 0))

    if applicable and actual != expected:
        codes = ", ".join(str(r.get("code")) for r in applicable)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tax total {actual} does not match jurisdiction snapshot {expected}; rules: {codes}",
        )
    if not applicable and actual != 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document has tax but the jurisdiction snapshot contains no applicable VAT/GST/sales-tax rule",
        )


def validate_payment_wht(payment: Any, snapshot: Any) -> None:
    """Validate settlement WHT against the payment snapshot, when WHT rules exist."""
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
    expected_rate = sum((_money(r.get("rate")) for r in rules), Decimal("0"))
    expected = _money(gross * expected_rate / Decimal("100"))
    if wht != expected:
        codes = ", ".join(str(r.get("code")) for r in rules)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"WHT {wht} does not match jurisdiction snapshot {expected}; rules: {codes}")
