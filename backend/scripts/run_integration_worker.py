"""PrimeERP automatic integration sync worker entrypoint."""
from app.database.session import SessionLocal
from app.modules.integrations.worker import run_forever


if __name__ == "__main__":
    run_forever(SessionLocal)
