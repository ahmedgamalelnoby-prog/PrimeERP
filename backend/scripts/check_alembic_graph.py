from __future__ import annotations

from pathlib import Path

from alembic.script import ScriptDirectory
from alembic.config import Config

BACKEND = Path(__file__).resolve().parents[1]
ALEMBIC_INI = BACKEND / "alembic.ini"


def fail(message: str) -> None:
    raise SystemExit(f"ALEMBIC GRAPH FAILED: {message}")


def main() -> int:
    config = Config(str(ALEMBIC_INI))
    script = ScriptDirectory.from_config(config)

    revisions = {}
    duplicate_ids = []
    for rev in script.walk_revisions():
        if rev.revision in revisions:
            duplicate_ids.append(rev.revision)
        revisions[rev.revision] = rev

    if duplicate_ids:
        fail(f"duplicate revision ids: {sorted(set(duplicate_ids))}")

    heads = list(script.get_heads())
    if len(heads) != 1:
        fail(f"expected exactly one Alembic head, found {len(heads)}: {heads}")

    # Alembic merge revisions must list only independent heads. A merge parent
    # that is already an ancestor of another parent causes RevisionMap bookkeeping
    # errors such as KeyError while advancing heads.
    for rev in revisions.values():
        parents = [p for p in rev._normalized_down_revisions if p]
        if len(parents) < 2:
            continue
        for parent in parents:
            for other in parents:
                if parent == other:
                    continue
                try:
                    ancestors = script.get_revision(other).iter_ancestors()
                    ancestor_ids = {item.revision for item in ancestors}
                except Exception as exc:
                    fail(f"cannot inspect merge {rev.revision}: {exc}")
                if parent in ancestor_ids:
                    fail(
                        f"merge {rev.revision} lists ancestor {parent} together with descendant {other}"
                    )

    # Every declared parent must resolve to a known revision unless it is a
    # symbolic base marker. Missing parents are otherwise easy to miss because
    # they surface only when Alembic loads the graph.
    for rev in revisions.values():
        for parent in rev._normalized_down_revisions:
            if parent and parent not in revisions:
                fail(f"revision {rev.revision} references missing parent {parent}")

    print(f"Alembic graph audit passed: {len(revisions)} revisions; head={heads[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
