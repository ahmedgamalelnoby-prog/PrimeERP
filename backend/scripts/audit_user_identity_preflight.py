from __future__ import annotations

import json
from typing import Any

from sqlalchemy import inspect, text

from app.database.session import engine


def _quote(connection, identifier: str) -> str:
    return connection.dialect.identifier_preparer.quote(identifier)


def _qualified(connection, schema: str | None, table: str) -> str:
    name = _quote(connection, table)
    return f"{_quote(connection, schema)}.{name}" if schema else name


def _duplicate_groups(connection, column: str) -> list[dict[str, Any]]:
    result = connection.execute(
        text(
            f"""
            SELECT lower(trim({column})) AS normalized_value,
                   array_agg(id ORDER BY id) AS user_ids,
                   count(*) AS row_count
            FROM public.users
            GROUP BY lower(trim({column}))
            HAVING count(*) > 1
            ORDER BY normalized_value
            """
        )
    ).mappings()
    return [dict(row) for row in result]


def _duplicate_primary_keys(connection) -> list[dict[str, Any]]:
    result = connection.execute(
        text(
            """
            SELECT id,
                   array_agg(ctid::text ORDER BY ctid) AS physical_tuples,
                   count(*) AS row_count
            FROM public.users
            GROUP BY id
            HAVING count(*) > 1
            ORDER BY id
            """
        )
    ).mappings()
    return [dict(row) for row in result]


def _foreign_key_references(connection, duplicate_ids: list[int]) -> list[dict[str, Any]]:
    if not duplicate_ids:
        return []

    inspector = inspect(connection)
    references: list[dict[str, Any]] = []
    for schema in inspector.get_schema_names():
        if schema in {"information_schema", "pg_catalog"}:
            continue
        for table in inspector.get_table_names(schema=schema):
            for foreign_key in inspector.get_foreign_keys(table, schema=schema):
                referred_schema = foreign_key.get("referred_schema") or "public"
                if referred_schema != "public" or foreign_key.get("referred_table") != "users":
                    continue

                local_columns = foreign_key.get("constrained_columns") or []
                remote_columns = foreign_key.get("referred_columns") or []
                if len(local_columns) != 1 or remote_columns != ["id"]:
                    references.append(
                        {
                            "table": f"{schema}.{table}" if schema else table,
                            "constraint": foreign_key.get("name"),
                            "status": "not_counted_composite_foreign_key",
                            "local_columns": local_columns,
                        }
                    )
                    continue

                local_column = _quote(connection, local_columns[0])
                table_name = _qualified(connection, schema, table)
                rows = connection.execute(
                    text(
                        f"""
                        SELECT {local_column} AS user_id, count(*) AS reference_count
                        FROM {table_name}
                        WHERE {local_column} = ANY(:user_ids)
                        GROUP BY {local_column}
                        ORDER BY {local_column}
                        """
                    ),
                    {"user_ids": duplicate_ids},
                ).mappings()
                for row in rows:
                    references.append(
                        {
                            "table": f"{schema}.{table}" if schema else table,
                            "constraint": foreign_key.get("name"),
                            "user_id": int(row["user_id"]),
                            "reference_count": int(row["reference_count"]),
                        }
                    )
    return references


def main() -> int:
    """Read-only diagnostic for duplicate global login identities and references."""
    if engine.dialect.name != "postgresql":
        raise SystemExit(
            "This audit requires PostgreSQL. No database changes were made."
        )

    with engine.connect() as connection:
        with connection.begin():
            connection.exec_driver_sql("SET TRANSACTION READ ONLY")
            # Force heap-based reads for this forensic preflight. An index lookup
            # can omit a heap tuple when an index is inconsistent, hiding the
            # condition this audit is intended to detect.
            connection.exec_driver_sql("SET LOCAL enable_indexscan = off")
            connection.exec_driver_sql("SET LOCAL enable_indexonlyscan = off")
            connection.exec_driver_sql("SET LOCAL enable_bitmapscan = off")

            duplicate_usernames = _duplicate_groups(connection, "username")
            duplicate_emails = _duplicate_groups(connection, "email")
            duplicate_primary_keys = _duplicate_primary_keys(connection)

            duplicate_ids = sorted(
                {
                    int(user_id)
                    for group in [*duplicate_usernames, *duplicate_emails]
                    for user_id in group["user_ids"]
                }
                | {int(group["id"]) for group in duplicate_primary_keys}
            )
            physical_rows: list[dict[str, Any]] = []
            if duplicate_ids:
                rows = connection.execute(
                    text(
                        """
                        SELECT ctid::text AS physical_tuple, id, tenant_id,
                               username, email, xmin::text AS inserting_transaction
                        FROM public.users
                        WHERE id = ANY(:user_ids)
                        ORDER BY id, ctid
                        """
                    ),
                    {"user_ids": duplicate_ids},
                ).mappings()
                physical_rows = [dict(row) for row in rows]

            references = _foreign_key_references(connection, duplicate_ids)

    report = {
        "status": "blocked"
        if duplicate_usernames or duplicate_emails or duplicate_primary_keys
        else "clean",
        "duplicate_usernames": duplicate_usernames,
        "duplicate_emails": duplicate_emails,
        "duplicate_primary_keys": duplicate_primary_keys,
        "physical_user_rows": physical_rows,
        "foreign_key_references": references,
        "mutations_performed": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))

    if report["status"] == "blocked":
        print(
            "Preflight failed. Review duplicate physical rows and all reported "
            "dependent records before attempting any repair."
        )
        return 1

    print("Preflight passed: no duplicate normalized usernames or emails.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
