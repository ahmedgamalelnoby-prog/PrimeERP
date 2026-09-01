"""Run subscription expiration from Windows Task Scheduler / cron.

Recommended schedule: every 15 minutes.
"""
from app.database.session import SessionLocal
from app.modules.platform.saas_core import refresh_expired_subscriptions


def main() -> None:
    db = SessionLocal()
    try:
        updated = refresh_expired_subscriptions(db)
        print(f"PrimeERP subscription expiration: updated={updated}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
