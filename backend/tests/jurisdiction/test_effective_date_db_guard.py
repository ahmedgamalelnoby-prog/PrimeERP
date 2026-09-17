import os
import threading
from datetime import date

import pytest
import psycopg
from psycopg.errors import ExclusionViolation


DATABASE_URL = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")


pytestmark = pytest.mark.integration


def _connect():
    if not DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL/DATABASE_URL is not configured")
    # The application uses SQLAlchemy's `postgresql+psycopg://` URL form,
    # while psycopg.connect() expects the standard PostgreSQL URI/conninfo form.
    conninfo = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://", 1)
    return psycopg.connect(conninfo)


def _setup(conn, table_name):
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
        cur.execute(f"DROP TABLE IF EXISTS {table_name}")
        cur.execute(
            f"""
            CREATE TABLE {table_name} (
                id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                company_id integer NOT NULL,
                jurisdiction_id integer NOT NULL,
                role text NOT NULL,
                effective_from date NOT NULL,
                effective_to date,
                is_active boolean NOT NULL DEFAULT true,
                CHECK (effective_to IS NULL OR effective_to >= effective_from),
                EXCLUDE USING gist (
                    company_id WITH =,
                    jurisdiction_id WITH =,
                    role WITH =,
                    daterange(effective_from, COALESCE(effective_to + 1, 'infinity'::date), '[)') WITH &&
                ) WHERE (is_active)
            )
            """
        )
    conn.commit()


def _cleanup(conn, table_name):
    with conn.cursor() as cur:
        cur.execute(f"DROP TABLE IF EXISTS {table_name}")
    conn.commit()


def test_database_rejects_open_ended_overlap_and_allows_different_keys():
    table_name = "_primeerp_effective_date_guard_test"
    with _connect() as conn:
        _setup(conn, table_name)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"INSERT INTO {table_name} (company_id, jurisdiction_id, role, effective_from, effective_to) VALUES (1, 10, 'tax', %s, NULL)",
                    (date(2026, 1, 1),),
                )
                with pytest.raises(ExclusionViolation):
                    cur.execute(
                        f"INSERT INTO {table_name} (company_id, jurisdiction_id, role, effective_from, effective_to) VALUES (1, 10, 'tax', %s, %s)",
                        (date(2026, 6, 1), date(2026, 12, 31)),
                    )
                cur.execute(
                    f"INSERT INTO {table_name} (company_id, jurisdiction_id, role, effective_from, effective_to) VALUES (2, 10, 'tax', %s, %s)",
                    (date(2026, 6, 1), date(2026, 12, 31)),
                )
            conn.commit()
        finally:
            _cleanup(conn, table_name)


def test_database_serializes_concurrent_overlap_inserts():
    table_name = "_primeerp_effective_date_guard_concurrency_test"
    setup_conn = _connect()
    _setup(setup_conn, table_name)
    setup_conn.close()

    barrier = threading.Barrier(2)
    first_committed = threading.Event()
    results = []

    def first_writer():
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"INSERT INTO {table_name} (company_id, jurisdiction_id, role, effective_from, effective_to) VALUES (7, 20, 'tax', %s, %s)",
                    (date(2027, 1, 1), date(2027, 12, 31)),
                )
            barrier.wait(timeout=10)
            conn.commit()
            first_committed.set()
            results.append("first_ok")

    def second_writer():
        with _connect() as conn:
            barrier.wait(timeout=10)
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        f"INSERT INTO {table_name} (company_id, jurisdiction_id, role, effective_from, effective_to) VALUES (7, 20, 'tax', %s, %s)",
                        (date(2027, 6, 1), date(2027, 12, 31)),
                    )
                conn.commit()
                results.append("second_ok")
            except ExclusionViolation:
                conn.rollback()
                results.append("second_exclusion")

    t1 = threading.Thread(target=first_writer)
    t2 = threading.Thread(target=second_writer)
    t1.start()
    t2.start()
    t1.join(timeout=20)
    t2.join(timeout=20)

    try:
        assert first_committed.is_set()
        assert results.count("first_ok") == 1
        assert results.count("second_exclusion") == 1
        assert "second_ok" not in results
    finally:
        cleanup_conn = _connect()
        _cleanup(cleanup_conn, table_name)
        cleanup_conn.close()
