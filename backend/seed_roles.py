"""
Seed script to create default admin user
Run: python seed_admin.py
"""

import asyncio
import sys
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import async_session, engine
from app.models.user import User
from app.models.role import Role
from app.core.security import get_password_hash

async def create_admin_user():
    """Create default admin user if not exists"""
    
    async with async_session() as session:
        try:
            # Check if admin already exists
            stmt = select(User).where(User.email == "admin@primeerp.com")
            result = await session.execute(stmt)
            existing_admin = result.scalar_one_or_none()
            
            if existing_admin:
                print("⚠️  Admin user already exists!")
                print(f"   Email: admin@primeerp.com")
                print(f"   Created at: {existing_admin.created_at}")
                return
            
            # Get admin role
            stmt = select(Role).where(Role.name == "admin")
            result = await session.execute(stmt)
            admin_role = result.scalar_one_or_none()
            
            if not admin_role:
                print("❌ Admin role not found! Please run seed_roles.py first.")
                return
            
            # Create admin user
            admin_user = User(
                email="admin@primeerp.com",
                username="admin",
                full_name="مدير النظام",
                hashed_password=get_password_hash("Admin@123"),
                is_active=True,
                is_superuser=True,
                role_id=admin_role.id,
                created_at=datetime.utcnow()
            )
            
            session.add(admin_user)
            await session.commit()
            
            print("✅ Admin user created successfully!")
            print("=" * 50)
            print("📧 Email: admin@primeerp.com")
            print("🔑 Password: Admin@123")
            print("👤 Role: Admin (Full Access)")
            print("=" * 50)
            print("⚠️  PLEASE CHANGE THE PASSWORD AFTER FIRST LOGIN!")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error creating admin user: {str(e)}")
            raise

async def main():
    """Main function"""
    print("🔄 Creating admin user...")
    print("-" * 50)
    
    try:
        await create_admin_user()
    except Exception as e:
        print(f"❌ Failed: {str(e)}")
        sys.exit(1)
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())