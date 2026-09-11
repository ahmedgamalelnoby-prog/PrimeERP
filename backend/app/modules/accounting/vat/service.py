from __future__ import annotations

from decimal import Decimal

from app.modules.accounting.taxes.service import TaxResult, TaxService


class VATService(TaxService):
    """VAT-specific façade over the common tax calculation contract."""

    def calculate_output_vat(self, net_amount: Decimal | int | float | str, rate: Decimal | int | float | str) -> TaxResult:
        return self.calculate(net_amount, rate)

    def extract_vat_from_gross(self, gross_amount: Decimal | int | float | str, rate: Decimal | int | float | str) -> TaxResult:
        return self.reverse_tax(gross_amount, rate)


vat_service = VATService()
