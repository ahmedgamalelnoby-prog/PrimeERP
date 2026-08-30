from app.core.database.mixins.audit_mixin import AuditMixin
from app.core.database.mixins.soft_delete_mixin import SoftDeleteMixin
from app.core.database.mixins.timestamp_mixin import TimestampMixin


class FullAuditMixin(
    TimestampMixin,
    AuditMixin,
    SoftDeleteMixin,
):
    """
    Combines timestamp, audit and soft delete mixins.
    """

    pass