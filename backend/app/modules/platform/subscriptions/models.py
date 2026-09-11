"""Canonical platform subscription boundary.

The physical subscriptions table remains owned by the legacy SaaS persistence
model during migration. This adapter prevents a second SQLAlchemy mapping for
the same table.
"""

from app.modules.saas.models import Subscription

__all__ = ["Subscription"]
