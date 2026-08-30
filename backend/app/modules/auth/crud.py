# المسار: D:\PrimeERP\backend\app\modules\auth\crud.py

from sqlalchemy.orm import Session
from app.modules.auth.models import User
from app.core.security import get_password_hash


class AuthCRUD:
    @staticmethod
    def get_user_by_username(db: Session, username: str):
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def create_user(db: Session, user_data: dict):
        user = User(
            username=user_data.get("username"),
            email=user_data.get("email"),
            full_name=user_data.get("full_name"),
            phone=user_data.get("phone"),
            address=user_data.get("address"),
            role_id=user_data.get("role_id"),
            hashed_password=get_password_hash(user_data.get("password")),
            is_active=user_data.get("is_active", True),
            is_superuser=user_data.get("is_superuser", False),
            must_change_password=user_data.get("must_change_password", False),
        )

        db.add(user)
        db.commit()
        db.refresh(user)
        return user
