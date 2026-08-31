from __future__ import annotations

import getpass
import os

from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.modules.identity.models import Role, User
from app.modules.identity.services.password_service import password_service

DEFAULT_EMAIL = "admin@primeerp.com"
DEFAULT_USERNAME = "admin"
DEFAULT_NAME = "PrimeERP System Administrator"
ROLE_NAME = "Super Admin"


def _get_password() -> str:
    value = os.getenv("PRIMEERP_SUPERADMIN_PASSWORD")
    if value:
        return value

    password = getpass.getpass("Super Admin password: ")
    confirmation = getpass.getpass("Confirm password: ")

    if not password:
        raise ValueError("Password cannot be empty.")
    if password != confirmation:
        raise ValueError("Passwords do not match.")
    if len(password) < 12:
        raise ValueError("Super Admin password must be at least 12 characters.")

    return password


def bootstrap_super_admin(
    db: Session,
    *,
    email: str = DEFAULT_EMAIL,
    username: str = DEFAULT_USERNAME,
    full_name: str = DEFAULT_NAME,
    password: str,
) -> User:
    email = email.strip().lower()
    username = username.strip().lower()

    role = db.query(Role).filter(Role.name == ROLE_NAME).first()
    if role is None:
        role = Role(
            name=ROLE_NAME,
            description="Full platform and tenant administration access.",
            is_active=True,
        )
        db.add(role)
        db.flush()

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        user = db.query(User).filter(User.username == username).first()

    if user is None:
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            hashed_password=password_service.hash_password(password),
            tenant_id=None,
            role_id=role.id,
            is_active=True,
            is_superuser=True,
            is_platform_admin=True,
            is_deleted=False,
            must_change_password=False,
            preferred_language="ar",
        )
        db.add(user)
    else:
        user.username = username
        user.email = email
        user.full_name = full_name
        user.tenant_id = None
        user.role_id = role.id
        user.is_active = True
        user.is_superuser = True
        user.is_platform_admin = True
        user.is_deleted = False
        user.must_change_password = False
        user.hashed_password = password_service.hash_password(password)

    db.commit()
    db.refresh(user)
    return user


def main() -> None:
    password = _get_password()
    db = SessionLocal()
    try:
        user = bootstrap_super_admin(db, password=password)
        print("Super Admin is ready.")
        print(f"Username: {user.username}")
        print(f"Email:    {user.email}")
        print(f"User ID:  {user.id}")
        print("Platform Admin: True")
        print("Superuser:      True")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
