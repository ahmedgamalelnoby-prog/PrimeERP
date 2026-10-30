from __future__ import annotations

import json

from sqlalchemy import text

from app.database.session import engine


def main() -> int:
    """Read-only diagnostic for duplicate global login identities."""
    if engine.dialect.name != "postgresql":
        raise SystemExit(
            "This audit requires PostgreSQL. No database changes were made."
        )

    with engine.connect() as connection:
        with connection.begin():
            connection.exec_driver_sql("SET TRANSACTION READ ONLY")

            duplicate_usernames = connection.execute(
                text(
                    """
                    SELECT lower(trim(username)) AS normalized_value,
                           array_agg(id ORDER BY id) AS user_ids,
                           count(*) AS row_count
                    FROM public.users
                    GROUP BY lower(trim(username))
                    HAVING count(*) > 1
                    ORDER BY normalized_value
                    """
                )
            ).mappings().all()

            duplicate_emails = connection.execute(
                text(
                    """
                    SELECT lower(trim(email)) AS normalized_value,
                           array_agg(id ORDER BY id) AS user_ids,
                           count(*) AS row_count
                    FROM public.users
                    GROUP BY lower(trim(email))
                    HAVING count(*) > 1
                    ORDER BY normalized_value
                    """
                )
            ).mappings().all()

            duplicate_ids = sorted(
                {
                    int(user_id)
                    for group in [*duplicate_usernames, *duplicate_emails]
                    for user_id in group["user_ids"]
                }
            )
            physical_rows = []
            if duplicate_ids:
                physical_rows = connection.execute(
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
                ).mappings().all()

    report = {
        "status": "blocked" if duplicate_usernames or duplicate_emails else "clean",
        "duplicate_usernames": [dict(row) for row in duplicate_usernames],
        "duplicate_emails": [dict(row) for row in duplicate_emails],
        "physical_user_rows": [dict(row) for row in physical_rows],
        "mutations_performed": False,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))

    if report["status"] == "blocked":
        print(
            "Preflight failed. Review physical rows and dependent records before "
            "attempting any repair or rerunning the identity migration."
        )
        return 1

    print("Preflight passed: no duplicate normalized usernames or emails.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
