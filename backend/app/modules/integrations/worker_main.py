from __future__ import annotations

import logging
import os
import signal
import time

from app.database.session import SessionLocal
from app.modules.integrations.worker import process_one_due_event

logger = logging.getLogger("primeerp.integration_worker")
STOP = False


def _stop(_signum, _frame):
    global STOP
    STOP = True


def run() -> None:
    interval = max(1, int(os.getenv("INTEGRATION_WORKER_INTERVAL_SECONDS", "2")))
    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)
    logger.info("PrimeERP integration worker started; interval=%ss", interval)

    while not STOP:
        db = SessionLocal()
        try:
            event = process_one_due_event(db)
            if event is None:
                time.sleep(interval)
            else:
                logger.info("Processed integration event id=%s status=%s", event.id, event.status)
        except Exception:
            db.rollback()
            logger.exception("Integration worker failed while processing an event")
            time.sleep(interval)
        finally:
            db.close()

    logger.info("PrimeERP integration worker stopped")


if __name__ == "__main__":
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    run()
