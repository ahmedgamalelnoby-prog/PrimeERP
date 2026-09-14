"""IFRS/CMA and Egypt compliance controls used at accounting boundaries."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any, Mapping

from app.modules.accounting.framework_registry import effective_ifrs_standards


class AccountingComplianceError(ValueError):
    """Raised when a transaction violates a configured accounting control."""


@dataclass(frozen=True)
class ComplianceContext:
    jurisdiction: str = "EG"
    accounting_framework: str = "IFRS"
    management_framework: str = "CMA"
    currency: str = "EGP"
    as_of: date = field(default_factory=date.today)


def validate_double_entry(lines: list[Mapping[str, Any]]) -> tuple[Decimal, Decimal]:
    if len(lines) < 2:
        raise AccountingComplianceError("A journal requires at least two lines")
    debit = Decimal("0")
    credit = Decimal("0")
    for index, line in enumerate(lines, 1):
        try:
            d = Decimal(str(line.get("debit", 0)))
            c = Decimal(str(line.get("credit", 0)))
        except Exception as exc:
            raise AccountingComplianceError(f"Invalid debit/credit on line {index}") from exc
        if not d.is_finite() or not c.is_finite() or d < 0 or c < 0 or (d > 0 and c > 0) or (d == 0 and c == 0):
            raise AccountingComplianceError(f"Invalid debit/credit on line {index}")
        debit += d
        credit += c
    if debit != credit:
        raise AccountingComplianceError(f"Unbalanced journal: debit={debit}, credit={credit}")
    return debit, credit


def validate_tax_totals(*, taxable_base: Decimal, output_tax: Decimal = Decimal("0"), withholding: Decimal = Decimal("0"), gross: Decimal | None = None) -> None:
    base = Decimal(taxable_base)
    vat = Decimal(output_tax)
    wht = Decimal(withholding)
    if base < 0 or vat < 0 or wht < 0:
        raise AccountingComplianceError("Tax amounts cannot be negative")
    expected_gross = base + vat
    if gross is not None and Decimal(gross) != expected_gross:
        raise AccountingComplianceError("Gross amount does not reconcile to taxable base plus output tax")
    if wht > expected_gross:
        raise AccountingComplianceError("Withholding tax cannot exceed gross consideration")


def validate_period(*, entry_date: date, start_date: date, end_date: date, status: str, allow_posting: bool = True) -> None:
    if status != "open" or not allow_posting:
        raise AccountingComplianceError("Accounting period is not open for posting")
    if not start_date <= entry_date <= end_date:
        raise AccountingComplianceError("Entry date is outside the accounting period")


def validate_source(*, source_module: str | None, source_entity: str | None, source_id: int | str | None) -> None:
    if not source_module or not source_entity or source_id in (None, ""):
        raise AccountingComplianceError("Posted journals require a traceable source transaction")


def validate_currency(currency: str, exchange_rate: Decimal = Decimal("1")) -> None:
    if len(currency or "") != 3 or not currency.isalpha():
        raise AccountingComplianceError("Currency must be an ISO-style three-letter code")
    if Decimal(exchange_rate) <= 0:
        raise AccountingComplianceError("Exchange rate must be positive")


def validate_ifrs_transaction(*, standard: str, context: Mapping[str, Any]) -> None:
    required: dict[str, tuple[str, ...]] = {
        "IAS_2": ("quantity", "unit_cost", "net_realizable_value"),
        "IAS_12": ("current_tax", "deferred_tax"),
        "IAS_16": ("asset_cost", "useful_life_months"),
        "IAS_21": ("currency", "exchange_rate"),
        "IAS_36": ("carrying_amount", "recoverable_amount"),
        "IAS_37": ("present_obligation", "probable_outflow", "reliably_estimable"),
        "IFRS_9": ("instrument_classification", "carrying_amount"),
        "IFRS_15": ("performance_obligation_satisfied", "consideration"),
        "IFRS_16": ("lease_term_months", "present_value_liability", "rou_asset"),
    }
    if standard not in required:
        return
    missing = [key for key in required[standard] if key not in context]
    if missing:
        raise AccountingComplianceError(f"{standard} transaction is missing: {', '.join(missing)}")
    if standard == "IAS_2":
        cost = Decimal(str(context["quantity"])) * Decimal(str(context["unit_cost"]))
        nrv = Decimal(str(context["net_realizable_value"]))
        if cost < 0 or nrv < 0:
            raise AccountingComplianceError("IAS 2 amounts cannot be negative")
        if cost > nrv and not context.get("impairment_recognized", False):
            raise AccountingComplianceError("IAS 2 requires a write-down when NRV is below cost")
    elif standard == "IAS_16" and int(context["useful_life_months"]) <= 0:
        raise AccountingComplianceError("IAS 16 useful life must be positive")
    elif standard == "IAS_21":
        validate_currency(str(context["currency"]), Decimal(str(context["exchange_rate"])))
    elif standard == "IAS_36":
        if Decimal(str(context["recoverable_amount"])) < Decimal(str(context["carrying_amount"])) and not context.get("impairment_recognized", False):
            raise AccountingComplianceError("IAS 36 impairment is required when recoverable amount is below carrying amount")
    elif standard == "IAS_37":
        if context["probable_outflow"] and context["reliably_estimable"] and not context.get("provision_recognized", False):
            raise AccountingComplianceError("IAS 37 provision recognition is required for a probable reliably estimable obligation")
        if context["probable_outflow"] and not context["reliably_estimable"] and context.get("provision_recognized", False):
            raise AccountingComplianceError("IAS 37 provision cannot be recognized without reliable estimation")
    elif standard == "IFRS_15":
        consideration = Decimal(str(context["consideration"]))
        if consideration < 0:
            raise AccountingComplianceError("IFRS 15 consideration cannot be negative")
        if not context["performance_obligation_satisfied"] and context.get("revenue_recognized", True):
            raise AccountingComplianceError("IFRS 15 revenue cannot be recognized before the performance obligation is satisfied")
    elif standard == "IFRS_16":
        if int(context["lease_term_months"]) <= 0 or Decimal(str(context["present_value_liability"])) < 0 or Decimal(str(context["rou_asset"])) < 0:
            raise AccountingComplianceError("IFRS 16 lease measurements are invalid")


def compliance_snapshot(context: ComplianceContext) -> dict[str, Any]:
    standards = effective_ifrs_standards(context.as_of) if context.accounting_framework == "IFRS" else []
    return {
        "jurisdiction": context.jurisdiction,
        "accounting_framework": context.accounting_framework,
        "management_framework": context.management_framework,
        "currency": context.currency,
        "as_of": context.as_of.isoformat(),
        "effective_ifrs_standards": standards,
        "legal_status": "configuration_required",
    }
