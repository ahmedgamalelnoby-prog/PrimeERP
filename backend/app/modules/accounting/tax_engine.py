from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.accounting.models import TaxRate

CENT = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def calculate_taxes(
    db: Session,
    *,
    company_id: int,
    amount: Decimal,
    tax_ids: list[int],
    inclusive: bool = False,
) -> dict:
    """Calculate VAT/custom taxes and withholding taxes consistently.

    VAT/custom taxes increase the invoice total. WHT is calculated as a
    withholding deduction and never increases the payable invoice total.
    For inclusive pricing, the taxable base is extracted from the tax stack.
    """
    if amount < 0:
        raise HTTPException(422, "Amount cannot be negative")
    if len(tax_ids) != len(set(tax_ids)):
        raise HTTPException(422, "Duplicate tax ids are not allowed")

    taxes = []
    if tax_ids:
        taxes = list(
            db.scalars(
                select(TaxRate).where(
                    TaxRate.company_id == company_id,
                    TaxRate.id.in_(tax_ids),
                    TaxRate.is_active.is_(True),
                )
            ).all()
        )
    found = {tax.id for tax in taxes}
    missing = [tax_id for tax_id in tax_ids if tax_id not in found]
    if missing:
        raise HTTPException(404, f"Tax rate(s) not found: {missing}")

    additive = [tax for tax in taxes if not tax.is_withholding]
    withholding = [tax for tax in taxes if tax.is_withholding]

    base = Decimal(amount)
    additive_total = Decimal("0")
    tax_details = []

    if inclusive and additive:
        divisor = Decimal("1") + sum((Decimal(t.rate) / Decimal("100") for t in additive), Decimal("0"))
        base = base / divisor

    for tax in additive:
        tax_amount = money(base * Decimal(tax.rate) / Decimal("100"))
        additive_total += tax_amount
        tax_details.append({
            "id": tax.id,
            "code": tax.code,
            "name": tax.name,
            "type": tax.tax_type,
            "rate": Decimal(tax.rate),
            "amount": tax_amount,
            "withholding": False,
        })

    gross = money(base + additive_total)
    withholding_total = Decimal("0")
    for tax in withholding:
        tax_amount = money(base * Decimal(tax.rate) / Decimal("100"))
        withholding_total += tax_amount
        tax_details.append({
            "id": tax.id,
            "code": tax.code,
            "name": tax.name,
            "type": tax.tax_type,
            "rate": Decimal(tax.rate),
            "amount": tax_amount,
            "withholding": True,
        })

    withholding_total = money(withholding_total)
    if withholding_total > gross:
        raise HTTPException(422, "Total withholding tax cannot exceed the gross taxable amount")

    payable = money(gross - withholding_total)
    return {
        "input_amount": money(Decimal(amount)),
        "taxable_base": money(base),
        "tax_total": money(additive_total),
        "gross_total": gross,
        "withholding_total": withholding_total,
        "payable_total": payable,
        "inclusive": inclusive,
        "taxes": tax_details,
    }
