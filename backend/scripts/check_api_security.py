from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "app"
PUBLIC_MUTATION_FILES = {
    "modules/identity/api/router.py",          # login, refresh, logout
    "modules/saas/router.py",                  # public tenant registration
    "modules/integrations/public_router.py",   # signed external webhooks
}
MUTATING = {"post", "put", "patch", "delete"}
AUTH_MARKERS = (
    "get_current_user",
    "get_current_user_for_billing",
    "require_permission",
    "require_platform_admin",
    "Depends(oauth2_scheme)",
)


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def has_auth_marker(node: ast.AST, source: str) -> bool:
    if any(marker in source for marker in AUTH_MARKERS):
        return True
    for child in ast.walk(node):
        if isinstance(child, ast.FunctionDef):
            for arg in (*child.args.args, *child.args.kwonlyargs):
                if arg.annotation is not None and any(name in ast.unparse(arg.annotation) for name in ("User", "CurrentUser")):
                    return True
    return False


def main() -> int:
    failures: list[str] = []
    for path in ROOT.rglob("*.py"):
        if not any(part in {"router.py", "routers.py"} or part.endswith("router.py") for part in [path.name]):
            if "/api/" not in path.as_posix().replace("\\", "/") and path.name not in {"public_router.py"}:
                continue
        rel = relative(path)
        if rel in PUBLIC_MUTATION_FILES:
            continue
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            failures.append(f"{rel}: syntax error: {exc}")
            continue

        has_mutation = False
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            decorators = [ast.unparse(d) for d in node.decorator_list]
            if any("@router." in d and any(f"router.{method}" in d for method in MUTATING) for d in decorators):
                has_mutation = True
                if not has_auth_marker(node, source):
                    failures.append(f"{rel}:{node.lineno} {node.name}: mutating API route has no authentication/authorization dependency")
        if has_mutation and "APIRouter" not in source:
            failures.append(f"{rel}: contains mutation decorators but no APIRouter declaration")

    if failures:
        print("API security boundary audit failed:")
        print("\n".join(f"- {item}" for item in failures))
        return 1
    print("API security boundary audit passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
