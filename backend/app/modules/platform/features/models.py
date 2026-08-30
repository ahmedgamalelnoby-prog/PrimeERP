from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.core.database.mixins import (
    FullAuditMixin,
    IdMixin,
    UUIDMixin,
)
from app.database.base import Base

from .constants import (
    FeatureCategory,
    FeatureStatus,
    FeatureType,
    FeatureValueType,
)

if TYPE_CHECKING:
    from app.modules.platform.plan_features.models import PlanFeature


class Feature(
    Base,
    IdMixin,
    UUIDMixin,
    FullAuditMixin,
):
    """
    Represents a licensable module, capability, limit or integration.

    Examples:
        accounting
        accounting.journal_entries
        limits.users
        integrations.whatsapp
    """

    __tablename__ = "features"

    code: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        unique=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    name_ar: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    display_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=FeatureCategory.SYSTEM.value,
        index=True,
    )

    feature_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=FeatureType.FUNCTION.value,
        index=True,
    )

    value_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=FeatureValueType.BOOLEAN.value,
    )

    default_value: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    icon: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    is_core: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    is_billable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    is_public: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=FeatureStatus.ACTIVE.value,
        index=True,
    )

    parent_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey(
            "features.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    parent: Mapped[Feature | None] = relationship(
        "Feature",
        remote_side="Feature.id",
        back_populates="children",
        foreign_keys=[parent_id],
    )

    children: Mapped[list[Feature]] = relationship(
        "Feature",
        back_populates="parent",
        foreign_keys=[parent_id],
        passive_deletes=True,
    )

    __table_args__ = (
        CheckConstraint(
            "sort_order >= 0",
            name="ck_features_sort_order_non_negative",
        ),
        CheckConstraint(
            "parent_id IS NULL OR parent_id <> id",
            name="ck_features_parent_not_self",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Feature("
            f"id={self.id}, "
            f"code='{self.code}', "
            f"type='{self.feature_type}'"
            f")>"
        )