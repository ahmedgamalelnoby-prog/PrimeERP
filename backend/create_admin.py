from app.database.session import SessionLocal
from app.database.models import User
from app.core.security import get_password_hash

db = SessionLocal()

existing = db.query(User).filter(User.email == "admin@example.com").first()

if existing:
    print("Admin already exists")
else:
    admin = User(
        email="admin@example.com",
        hashed_password=get_password_hash("admin123"),
        full_name="Administrator",
        role="admin",
        is_active=True
    )

    db.add(admin)
    db.commit()
    print("Admin created successfully")

db.close()