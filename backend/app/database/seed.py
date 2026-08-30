from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.core.authentication import get_password_hash
from app.modules.users.models import User
from app.modules.auth.models import Role

def create_super_admin():
    db = SessionLocal()
    try:
        # التحقق من وجود المستخدم
        admin = db.query(User).filter(User.email == "admin@primeerp.com").first()
        if not admin:
            # إنشاء دور المدير
            admin_role = Role(name="Super Admin", description="Full system access")
            db.add(admin_role)
            db.flush()
            
            # إنشاء المدير
            admin = User(
                email="admin@primeerp.com",
                username="admin",
                full_name="System Administrator",
                hashed_password=get_password_hash("Admin@123"),
                role_id=admin_role.id,
                is_active=True,
                is_superuser=True
            )
            db.add(admin)
            db.commit()
            print("✅ Super Admin created successfully!")
            print("📧 Email: admin@primeerp.com")
            print("🔑 Password: Admin@123")
        else:
            print("ℹ️ Super Admin already exists")
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_super_admin()