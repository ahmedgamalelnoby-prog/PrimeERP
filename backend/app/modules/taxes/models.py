"""Canonical tax-domain model exports.

TaxRate remains physically owned by Accounting to preserve the existing
ledger/database contract. The tax module re-exports it instead of defining a
second TaxRate table.
"""

from app.modules.accounting.models import TaxRate

__all__ = ["TaxRate"]
