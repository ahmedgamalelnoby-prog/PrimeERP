from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "app"
PUBLIC_MUTATION_FILES = {
    "modules/identity/api/router.py",
    "modules/saas/router.py",
}
PUBLIC_ROUTER_NAMES = {
    "modules/integrations/router.py": {"public_router"},
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


def router_auth_map(tree: ast.AST) -> dict[str, bool]:
    result: dict[str, bool] = {}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        value = node.value
        if not isinstance(value, ast.Call) or dependency_name(value.func) != "APIRouter":
            continue
        dependencies = next((keyword.value for keyword in value.keywords if keyword.arg == "dependencies"), None)
        names: list[str] = []
        if isinstance(node, ast.Assign):
            names = [target.id for target in node.targets if isinstance(target, ast.Name)]
        elif isinstance(node.target, ast.Name):
            names = [node.target.id]
        authorized = contains_authorizing_dep(dependencies)
        for name in names:
            result[name] = authorized
    return result


def route_router_name(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
    for decorator in node.decorator_list:
        if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
            continue
        if decorator.func.attr not in MUTATING:
            continue
        value = decorator.func.value
        if isinstance(value, ast.Name):
            return value.id
    return None


def is_explicitly_public_mutation(path: Path, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    rel = relative(path)
    if rel in PUBLIC_MUTATION_FILES:
        decorators = [ast.unparse(d) for d in node.decorator_list]
        return any(
            any(f"router.{method}" in decorator for method in MUTATING)
            for decorator in decorators
        )
    return route_router_name(node) in PUBLIC_ROUTER_NAMES.get(rel, set())


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

        router_auth = router_auth_map(tree)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            decorators = [ast.unparse(d) for d in node.decorator_list]
            mutation_decorators = [
                decorator
                for decorator in decorators
                if any(f".{method}" in decorator for method in MUTATING)
            ]
            if not mutation_decorators:
                continue
            if is_explicitly_public_mutation(path, node):
                continue
            if function_has_auth(node):
                continue
            router_name = route_router_name(node)
            if router_name and router_auth.get(router_name, False):
                continue
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
