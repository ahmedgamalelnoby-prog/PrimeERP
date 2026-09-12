from datetime import datetime, timedelta, timezone
import hashlib
import secrets

from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.identity.models.refresh_token import RefreshToken


class RefreshTokenService:
    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def issue(self, db: Session, user_id: int) -> str:
        token = secrets.token_urlsafe(48)
        expires_at = datetime.now(timezone.utc) + timedelta(days=int(settings.REFRESH_TOKEN_EXPIRE_DAYS))
        db.add(RefreshToken(user_id=user_id, token_hash=self.hash_token(token), expires_at=expires_at))
        return token

    def consume(self, db: Session, token: str) -> RefreshToken | None:
        now = datetime.now(timezone.utc)
        instance = (
            db.query(RefreshToken)
            .filter(RefreshToken.token_hash == self.hash_token(token))
            .with_for_update()
            .first()
        )
        if instance is None or not instance.is_active or instance.revoked_at is not None or instance.expires_at <= now:
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


refresh_token_service = RefreshTokenService()
