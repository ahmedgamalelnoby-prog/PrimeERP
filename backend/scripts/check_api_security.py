from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "app"
PUBLIC_MUTATION_FILES = {
    "modules/identity/api/router.py",
    "modules/saas/router.py",
    "modules/integrations/public_router.py",
}
MUTATING = {"post", "put", "patch", "delete"}
AUTH_DEPENDENCIES = {
    "get_current_user",
    "get_current_user_for_billing",
    "require_permission",
    "require_platform_admin",
    "oauth2_scheme",
    "_require_eta_notification_secret",
}


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def dependency_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Call):
        return dependency_name(node.func)
    return None


def contains_authorizing_dep(node: ast.AST | None) -> bool:
    if node is None:
        return False
    for current in ast.walk(node):
        if not isinstance(current, ast.Call):
            continue
        if dependency_name(current.func) != "Depends":
            continue
        if current.args and dependency_name(current.args[0]) in AUTH_DEPENDENCIES:
            return True
    return False


def function_has_auth(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for decorator in node.decorator_list:
        if contains_authorizing_dep(decorator):
            return True
    for default in [*node.args.defaults, *node.args.kw_defaults]:
        if contains_authorizing_dep(default):
            return True
    return False


def router_has_auth(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        value = node.value
        if not isinstance(value, ast.Call) or dependency_name(value.func) != "APIRouter":
            continue
        dependencies = next((keyword.value for keyword in value.keywords if keyword.arg == "dependencies"), None)
        if contains_authorizing_dep(dependencies):
            return True
    return False


def is_explicitly_public_mutation(path: Path, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    if relative(path) not in PUBLIC_MUTATION_FILES:
        return False
    decorators = [ast.unparse(d) for d in node.decorator_list]
    return any(
        any(f"router.{method}" in decorator for method in MUTATING)
        for decorator in decorators
    )


def main() -> int:
    failures: list[str] = []
    for path in ROOT.rglob("*.py"):
        rel = relative(path)
        normalized = path.as_posix()
        if path.name not in {"router.py", "routers.py", "public_router.py"} and "/api/" not in normalized:
            continue
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            failures.append(f"{rel}: syntax error: {exc}")
            continue

        router_level_auth = router_has_auth(tree)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            decorators = [ast.unparse(d) for d in node.decorator_list]
            mutation_decorators = [
                decorator
                for decorator in decorators
                if any(f"router.{method}" in decorator for method in MUTATING)
            ]
            if not mutation_decorators or is_explicitly_public_mutation(path, node):
                continue
            if not (router_level_auth or function_has_auth(node)):
                failures.append(
                    f"{rel}:{node.lineno} {node.name}: mutating API route has no real FastAPI authentication/authorization dependency"
                )

    if failures:
        print("API security boundary audit failed:")
        print("\n".join(f"- {item}" for item in failures))
        return 1
    print("API security boundary audit passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
