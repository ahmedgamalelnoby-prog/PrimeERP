"""PrimeERP scheduled report worker entrypoint."""
from app.database.session import SessionLocal
from app.modules.reports.worker import run_forever


if __name__ == "__main__":
    run_forever(SessionLocal)
