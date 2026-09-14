import ast
from pathlib import Path

from scripts import check_api_security


ROOT = Path(__file__).resolve().parents[1]


def _load_tree(relative_path: str) -> ast.Module:
    path = ROOT / relative_path
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _function(tree: ast.Module, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    raise AssertionError(f"Function not found: {name}")


def test_security_checker_scopes_authentication_to_each_router() -> None:
    path = ROOT / "app/modules/integrations/router.py"
    tree = _load_tree("app/modules/integrations/router.py")
    router_auth = check_api_security.router_auth_map(tree)

    assert router_auth["router"] is True
    assert router_auth["public_router"] is False

    public_handler = _function(tree, "receive_salla_webhook_public")
    authenticated_handler = _function(tree, "create_connection")

    assert check_api_security.route_router_name(public_handler) == "public_router"
    assert check_api_security.route_router_name(authenticated_handler) == "router"
    assert check_api_security.is_explicitly_public_mutation(path, public_handler) is True
    assert check_api_security.is_explicitly_public_mutation(path, authenticated_handler) is False
