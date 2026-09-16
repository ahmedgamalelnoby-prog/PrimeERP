from __future__ import annotations

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

BACKEND = Path(__file__).resolve().parents[1]
ALEMBIC_INI = BACKEND / "alembic.ini"


def fail(message: str) -> None:
    raise SystemExit(f"ALEMBIC GRAPH FAILED: {message}")


def _parents(revision) -> tuple[str, ...]:
    """Return concrete parent revision ids for an Alembic Script node."""
    return tuple(parent for parent in revision._normalized_down_revisions if parent)


def _is_ancestor(candidate: str, descendant: str, parent_map: dict[str, tuple[str, ...]]) -> bool:
    """Return True when candidate is reachable from descendant's parents."""
    stack = list(parent_map.get(descendant, ()))
    seen: set[str] = set()
    while stack:
        current = stack.pop()
        if current == candidate:
            return True
        if current in seen:
            continue
        seen.add(current)
        stack.extend(parent_map.get(current, ()))
    return False


def _find_cycle(parent_map: dict[str, tuple[str, ...]]) -> list[str] | None:
    """Find one revision cycle, if any, using DFS over parent edges."""
    visiting: set[str] = set()
    visited: set[str] = set()
    path: list[str] = []

    def visit(node: str) -> list[str] | None:
        if node in visiting:
            try:
                start = path.index(node)
            except ValueError:
                start = 0
            return path[start:] + [node]
        if node in visited:
            return None

        visiting.add(node)
        path.append(node)
        for parent in parent_map.get(node, ()):
            cycle = visit(parent)
            if cycle:
                return cycle
        path.pop()
        visiting.remove(node)
        visited.add(node)
        return None

    for node in parent_map:
        cycle = visit(node)
        if cycle:
            return cycle
    return None


def main() -> int:
    config = Config(str(ALEMBIC_INI))
    script = ScriptDirectory.from_config(config)

    revisions: dict[str, object] = {}
    duplicate_ids: list[str] = []
    for rev in script.walk_revisions():
        if rev.revision in revisions:
            duplicate_ids.append(rev.revision)
        revisions[rev.revision] = rev

    if duplicate_ids:
        fail(f"duplicate revision ids: {sorted(set(duplicate_ids))}")

    parent_map = {revision_id: _parents(rev) for revision_id, rev in revisions.items()}

    # Validate parent references before doing ancestry traversal so a malformed
    # graph fails with the actual missing revision rather than a later KeyError.
    for revision_id, parents in parent_map.items():
        for parent in parents:
            if parent not in revisions:
                fail(f"revision {revision_id} references missing parent {parent}")

    cycle = _find_cycle(parent_map)
    if cycle:
        fail(f"migration graph contains a cycle: {' -> '.join(cycle)}")

    heads = list(script.get_heads())
    if len(heads) != 1:
        fail(f"expected exactly one Alembic head, found {len(heads)}: {heads}")

    # A merge must contain only independent heads. If one declared parent is an
    # ancestor of another, Alembic can fail while advancing the revision map.
    for revision_id, parents in parent_map.items():
        if len(parents) < 2:
            continue
        for index, parent in enumerate(parents):
            for other in parents[index + 1 :]:
                if _is_ancestor(parent, other, parent_map):
                    fail(
                        f"merge {revision_id} lists ancestor {parent} together with descendant {other}"
                    )
                if _is_ancestor(other, parent, parent_map):
                    fail(
                        f"merge {revision_id} lists ancestor {other} together with descendant {parent}"
                    )

    print(f"Alembic graph audit passed: {len(revisions)} revisions; head={heads[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
