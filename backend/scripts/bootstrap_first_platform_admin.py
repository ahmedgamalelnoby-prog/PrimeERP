"""Safely provision the first PrimeERP platform administrator.

Run inside the backend container only on a fresh installation with no users.
Credentials are prompted interactively and are never stored in source code or
printed to the terminal.
"""

from __future__ import annotations

import getpass
import re
from sqlalchemy import func, text

# Import model classes before opening the session so the ORM registry is complete.
from app.database.session import SessionLocal
from app.modules.identity.models.user import User
from app.modules.identity.services.password_service import password_service
from app.modules.roles.models import Role  # noqa: F401
from app.modules.saas.models import Tenant  # noqa: F401
from app.modules.companies.models import Company  # noqa: F401
from app.modules.branches.models import Branch  # noqa: F401


def prompt_nonempty(label: str, *, max_length: int) -> str:
    while True:
        value = input(label).strip()
        if value and len(value) <= max_length:
            return value
        print(f"Enter a value between 1 and {max_length} characters.")


def main() -> int:
    print("PrimeERP — first platform administrator bootstrap")
    print("This operation is allowed only when the database has no user accounts.")
    print("Use a unique username/email and a strong password.")
    confirmation = input("Type CREATE-FIRST-ADMIN to continue: ").strip()
    if confirmation != "CREATE-FIRST-ADMIN":
        print("Cancelled; no changes made.")
        return 1

    username = prompt_nonempty("Username (English letters, numbers, _ or -): ", max_length=50).lower()
    if not re.fullmatch(r"[a-zA-Z0-9_-]{3,50}", username):
        print("Username must be 3–50 characters and contain only English letters, numbers, underscores or hyphens.")
        return 1

    email = prompt_nonempty("Email: ", max_length=150).lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        print("Enter a valid email address.")
        return 1

    full_name = prompt_nonempty("Administrator full name: ", max_length=150)
    password = getpass.getpass("New password (minimum 12 characters): ")
    confirm_password = getpass.getpass("Confirm password: ")
    if password != confirm_password:
        print("Passwords do not match.")
        return 1
    if len(password) < 12 or len(password.encode("utf-8")) > 72:
        print("Password must be at least 12 characters and no more than 72 UTF-8 bytes.")
        return 1
    if not any(c.islower() for c in password) or not any(c.isupper() for c in password) or not any(c.isdigit() for c in password):
        print("Password must include at least one uppercase letter, one lowercase letter and one number.")
        return 1

    db = SessionLocal()
    try:
        # Serialize bootstrap attempts so two concurrent invocations cannot both pass the empty check.
        db.execute(text("SELECT pg_advisory_xact_lock(726190314, 1)"))
        existing_users = db.query(func.count(User.id)).scalar() or 0
        existing_admins = db.query(func.count(User.id)).filter(
            User.is_platform_admin.is_(True),
            User.is_deleted.is_(False),
        ).scalar() or 0
        if existing_users != 0 or existing_admins != 0:
            print("Refusing to bootstrap: user accounts already exist. Use the authenticated admin workflow instead.")
            return 2

        user = User(
            tenant_id=None,
            username=username,
            email=email,
            full_name=full_name,
            hashed_password=password_service.hash_password(password),
            preferred_language="ar",
            is_active=True,
            is_superuser=True,
            is_platform_admin=True,
            is_deleted=False,
            must_change_password=False,
            role_id=None,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Platform administrator created successfully (user id: {user.id}).")
        print("Sign in at http://localhost:3001 using the username or email and the password you just set.")
        return 0
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled; no changes made.")
        raise SystemExit(130)
