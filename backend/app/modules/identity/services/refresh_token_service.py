from datetime import datetime, timedelta, timezone
import hashlib
import secrets

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.identity.models.refresh_token import RefreshToken


class RefreshTokenReuseError(Exception):
    """Raised when an already-rotated refresh token is presented again."""


class RefreshTokenService:
    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def new_family_id() -> str:
        return secrets.token_hex(32)

    def issue(self, db: Session, user_id: int, family_id: str | None = None) -> str:
        token = secrets.token_urlsafe(48)
        expires_at = datetime.now(timezone.utc) + timedelta(days=int(settings.REFRESH_TOKEN_EXPIRE_DAYS))
        db.add(
            RefreshToken(
                user_id=user_id,
                token_hash=self.hash_token(token),
                family_id=family_id or self.new_family_id(),
                expires_at=expires_at,
            )
        )
        return token

    def consume(self, db: Session, token: str) -> RefreshToken | None:
        now = datetime.now(timezone.utc)
        instance = (
            db.query(RefreshToken)
            .filter(RefreshToken.token_hash == self.hash_token(token))
            .with_for_update()
            .first()
        )
        if instance is None:
            return None
        if instance.replaced_by_id is not None:
            self.revoke_family(db, instance.family_id, now=now)
            raise RefreshTokenReuseError("Refresh token reuse detected")
        if not instance.is_active or instance.revoked_at is not None or instance.expires_at <= now:
            return None
        instance.is_active = False
        instance.revoked_at = now
        return instance

    def revoke(self, db: Session, token: str) -> bool:
        """Revoke a refresh token during logout. Missing/already-revoked tokens are idempotent."""
        now = datetime.now(timezone.utc)
        instance = (
            db.query(RefreshToken)
            .filter(RefreshToken.token_hash == self.hash_token(token))
            .with_for_update()
            .first()
        )
        if instance is None:
            return False
        if instance.is_active:
            instance.is_active = False
            instance.revoked_at = now
        return True

    def revoke_family(self, db: Session, family_id: str, *, now: datetime | None = None) -> int:
        now = now or datetime.now(timezone.utc)
        result = db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.family_id == family_id,
                RefreshToken.is_active.is_(True),
            )
            .values(is_active=False, revoked_at=now)
        )
        return int(result.rowcount or 0)


refresh_token_service = RefreshTokenService()
