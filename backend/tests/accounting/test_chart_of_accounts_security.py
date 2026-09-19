import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ROUTER = ROOT / "app/modules/accounting/chart_of_accounts/router.py"


def _tree() -> ast.Module:
    return ast.parse(ROUTER.read_text(encoding="utf-8"), filename=str(ROUTER))


def _route_functions(tree: ast.Module):
    return {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("list_")
    }


def _source_contains_call(node: ast.AST, name: str) -> bool:
    return any(
        isinstance(current, ast.Call)
        and (
            isinstance(current.func, ast.Name)
            and current.func.id == name
            or isinstance(current.func, ast.Attribute)
            and current.func.attr == name
        )
        for current in ast.walk(node)
    )


def test_chart_of_accounts_reads_require_authenticated_tenant_context() -> None:
    tree = _tree()
    routes = _route_functions(tree)
    assert set(routes) == {
        "list_departments",
        "list_cost_centers",
        "list_natural_accounts",
        "list_account_combinations",
    }

    source = ROUTER.read_text(encoding="utf-8")
    assert "get_current_user" in source
    assert "require_permission(\"accounting.chart_of_accounts.read\")" in source
    assert "get_effective_tenant_id" in source
    assert "Company.tenant_id == tenant_id" in source

    for route in routes.values():
        assert _source_contains_call(route, "_authorized_company")
