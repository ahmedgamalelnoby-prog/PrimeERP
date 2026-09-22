"""PostgreSQL-backed POS replay/concurrency guard tests."""
import os
import threading
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

def _database_url():
    return os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")

@pytest.mark.integration
def test_sales_invoice_replay_guard_exists_in_postgresql():
    url = _database_url()
    if not url:
        pytest.skip("TEST_DATABASE_URL/DATABASE_URL is not configured")
    engine = create_engine(url, pool_pre_ping=True)
    with engine.connect() as conn:
        row = conn.execute(text(
            "SELECT indexname, indexdef FROM pg_indexes "
            "WHERE schemaname = current_schema() "
            "AND tablename = 'sales_documents' "
            "AND indexname = 'uq_sales_documents_company_invoice_number'"
        )).first()
    engine.dispose()
    assert row is not None
    assert "UNIQUE" in row.indexdef.upper()
    assert "company_id" in row.indexdef
    assert "number" in row.indexdef
    assert "document_type" in row.indexdef and "invoice" in row.indexdef

@pytest.mark.integration
def test_postgresql_rejects_concurrent_duplicate_invoice_identity():
    url = _database_url()
    if not url:
        pytest.skip("TEST_DATABASE_URL/DATABASE_URL is not configured")
    engine = create_engine(url, pool_size=4, max_overflow=0, pool_pre_ping=True)
    table = "pos_replay_probe_" + uuid4().hex
    barrier = threading.Barrier(2)
    results = []
    errors = []

    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE " + table + " ("
            "id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,"
            "company_id text NOT NULL,"
            "number text NOT NULL,"
            "document_type text NOT NULL)"
        ))
        conn.execute(text(
            "CREATE UNIQUE INDEX " + table + "_uq_invoice_identity "
            "ON " + table + " (company_id, number) "
            "WHERE document_type = 'invoice'"
        ))

    def attempt():
        try:
            with engine.begin() as conn:
                barrier.wait(timeout=10)
                conn.execute(
                    text(
                        "INSERT INTO " + table +
                        "(company_id, number, document_type) "
                        "VALUES (:company_id, :number, 'invoice')"
                    ),
                    {"company_id": "company-1", "number": "OFFLINE-CONCURRENT-0001"},
                )
                results.append("committed")
        except IntegrityError:
            errors.append("duplicate")

    threads = [threading.Thread(target=attempt) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=15)

    try:
        assert sorted(results + errors) == ["committed", "duplicate"]
    finally:
        with engine.begin() as conn:
            conn.execute(text("DROP TABLE " + table))
        engine.dispose()
