from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    Index,
    String,
    Text,
    TIMESTAMP,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base
from app.modules.roles.models import Role
from app.modules.saas.models import Tenant


class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    tenant_id = Column(
        Integer,
        ForeignKey(
            "tenants.id",
            ondelete="CASCADE",
        ),
        nullable=True,
        index=True,
    )

    username = Column(
        String(50),
        nullable=False,
        index=True,
    )

    email = Column(
        String(150),
        nullable=False,
        index=True,
    )

    full_name = Column(
        String(150),
        nullable=True,
    )

    phone = Column(
        String(30),
        nullable=True,
    )

    address = Column(
        Text,
        nullable=True,
    )

    profile_image = Column(
        String(500),
        nullable=True,
    )

    hashed_password = Column(
        String(255),
        nullable=False,
    )

    preferred_language = Column(
        String(5),
        nullable=False,
        default="ar",
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    is_superuser = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    is_platform_admin = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    is_deleted = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    must_change_password = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    role_id = Column(
        Integer,
        ForeignKey(
            "roles.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    last_login = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )

    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Import the related classes explicitly so User can also be imported
    # directly by scripts/tests without depending on a separate registry
    # import to resolve SQLAlchemy string relationships.
    tenant = relationship(
        Tenant,
        back_populates="users",
        foreign_keys=[tenant_id],
    )

    role = relationship(
        Role,
        back_populates="users",
        foreign_keys=[role_id],
    )

    __table_args__ = (
        Index("uq_users_username_global_ci", func.lower(username), unique=True),
        Index("uq_users_email_global_ci", func.lower(email), unique=True),
    )

    def __repr__(self) -> str:
        return (
            f"<User "
            f"id={self.id} "
            f"tenant_id={self.tenant_id} "
            f"username={self.username!r}>"
        )
