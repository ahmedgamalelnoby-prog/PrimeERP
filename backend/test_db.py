from app.database.session import engine
from sqlalchemy import text
from app.core.config import settings

def test_connection():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Connected to PostgreSQL!")
            print(f"📊 Version: {version}")
            print(f"📁 Database: {settings.POSTGRES_DB}")
            return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()