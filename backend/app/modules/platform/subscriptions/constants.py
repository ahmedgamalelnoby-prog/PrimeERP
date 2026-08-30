from enum import Enum


class SubscriptionStatus(str, Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class SubscriptionChangeType(str, Enum):
    NEW = "new"
    UPGRADE = "upgrade"
    DOWNGRADE = "downgrade"
    RENEWAL = "renewal"
    CANCELLATION = "cancellation"


class CancellationReason(str, Enum):
    CUSTOMER_REQUEST = "customer_request"
    PAYMENT_FAILED = "payment_failed"
    POLICY_VIOLATION = "policy_violation"
    ADMINISTRATIVE = "administrative"
    OTHER = "other"