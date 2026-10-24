"""Workflow adapters for company-scoped policy settings.

These adapters centralize policy reads and deterministic decisions. Owning modules
should call them at the transaction boundary (before writing/posting/syncing).
"""
from .approvals import approval_escalation_due, approval_mode, payroll_approval_required
from .general import format_company_date
from .hr import attendance_source_allowed, biometric_sync_due
from .integrations import automatic_sync_enabled, integration_sync_due
from .pos import cash_drawer_open_allowed

__all__ = [
    "approval_escalation_due",
    "approval_mode",
    "attendance_source_allowed",
    "automatic_sync_enabled",
    "biometric_sync_due",
    "cash_drawer_open_allowed",
    "format_company_date",
    "integration_sync_due",
    "payroll_approval_required",
]
