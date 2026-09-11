from __future__ import annotations

import logging
import os
import signal
import time

from app.database.session import SessionLocal
from .worker import process_one_due_event

logger = logging.getLogger("primeerp.integration_worker")
_STOP = False


def _stop(_signum, _frame) -> None:
    global _STOP
    _STOP = True


def main() -> None:
    interval = max(1.0, float(os.getenv("INTEGRATION_WORKER_INTERVAL_SECONDS", "2")))
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    logger.info("PrimeERP integration worker started")
    while not _STOP:
        db = SessionLocal()
        try:
            event = process_one_due_event(db)
            if event is None:
                db.rollback()
                time.sleep(interval)
        except Exception:
            db.rollback()
            logger.exception("Integration worker iteration failed")
            time.sleep(interval)
        finally:
            db.close()
    logger.info("PrimeERP integration worker stopped")


if __name__ == "__main__":
    main()
