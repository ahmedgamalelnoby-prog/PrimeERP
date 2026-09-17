from __future__ import annotations

import ast
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine, inspect, text

from app.core.module_engine.catalog import catalog_keys
from app.core.module_engine.identity import ALIASES, BUSINESS_TO_TECHNICAL

MODULE_ROOT = ROOT / "app" / "modules"
BUSINESS_CODES = frozenset(BUSINESS_TO_TECHNICAL)
PLAN_CODES = ("trial", "starter", "professional")


def fail(message: str) -> None:
    raise SystemExit(f"MODULE ENTITLEMENT CONTRACT FAILED: {message}")


def literal_string(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def scan_guard_calls() -> list[tuple[str, int, str, str]]:
    findings: list[tuple[str, int, str, str]] = []
    guard_names = {"require_module", "tenant_has_module", "require_entitlement"}
    for path in MODULE_ROOT.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            fail(f"cannot parse {path.relative_to(ROOT)}: {exc}")
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not node.args:
                continue
            name = call_name(node)
            if name not in guard_names:
                continue
            code = literal_string(node.args[0])
            if code is not None:
                findings.append((str(path.relative_to(ROOT)), node.lineno, name, code))
    return findings


def audit_static_contract() -> None:
    technical_catalog = catalog_keys()
    missing_technical = sorted(
        {technical for modules in BUSINESS_TO_TECHNICAL.values() for technical in modules}
        - technical_catalog
    )
    if missing_technical:
        fail(f"identity references technical modules absent from module catalog: {missing_technical}")

    for alias, target in ALIASES.items():
        if target not in BUSINESS_CODES:
            fail(f"alias {alias!r} points to non-canonical business code {target!r}")

    allowed = BUSINESS_CODES | set(ALIASES)
    unknown = [
        f"{path}:{line}: {guard}({code!r})"
        for path, line, guard, code in scan_guard_calls()
        if code not in allowed
    ]
    if unknown:
        fail("unknown module/entitlement codes found:\n" + "\n".join(sorted(unknown)))


def audit_database_contract() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        fail("DATABASE_URL is required for the database contract audit")
    engine = create_engine(database_url)
    inspector = inspect(engine)
    required_tables = {"system_modules", "plans", "subscription_plans", "plan_modules", "tenant_modules", "subscriptions"}
    missing_tables = sorted(required_tables - set(inspector.get_table_names()))
    if missing_tables:
        fail(f"required entitlement tables are missing: {missing_tables}")

    with engine.begin() as conn:
        modules = dict(conn.execute(text("SELECT code, id FROM system_modules WHERE is_active = true")).all())
        missing_identity_modules = sorted(BUSINESS_CODES - modules.keys())
        if missing_identity_modules:
            fail(f"business modules from identity are missing from system_modules: {missing_identity_modules}")

        duplicates = conn.execute(text("SELECT code, COUNT(*) FROM system_modules GROUP BY code HAVING COUNT(*) > 1")).all()
        if duplicates:
            fail(f"duplicate system module codes: {duplicates}")

        einvoice_count = conn.execute(text("SELECT COUNT(*) FROM system_modules WHERE code IN ('einvoice', 'egyptian_einvoice')")).scalar_one()
        if einvoice_count != 1:
            fail("e-invoice must have exactly one canonical system_modules row")

        plans = dict(conn.execute(text("SELECT code, id FROM plans WHERE is_deleted = false")).all())
        legacy = dict(conn.execute(text("SELECT code, id FROM subscription_plans")).all())
        missing_plans = sorted(set(PLAN_CODES) - plans.keys())
        if missing_plans:
            fail(f"canonical plans missing: {missing_plans}")
        for code in PLAN_CODES:
            if legacy.get(code) != plans.get(code):
                fail(f"plan identity mismatch for {code}: plans.id={plans.get(code)}, subscription_plans.id={legacy.get(code)}")

        dangling = conn.execute(text("""
            SELECT pm.id
            FROM plan_modules pm
            LEFT JOIN subscription_plans p ON p.id = pm.plan_id
            LEFT JOIN system_modules m ON m.id = pm.module_id
            WHERE p.id IS NULL OR m.id IS NULL
        """)).all()
        if dangling:
            fail(f"dangling plan_modules rows: {len(dangling)}")

        for plan_code in PLAN_CODES:
            count = conn.execute(text("""
                SELECT COUNT(*)
                FROM plan_modules pm
                JOIN subscription_plans p ON p.id = pm.plan_id
                JOIN system_modules m ON m.id = pm.module_id
                WHERE p.code = :code AND m.is_active = true AND pm.is_enabled = true
            """), {"code": plan_code}).scalar_one()
            if count == 0:
                fail(f"plan {plan_code} has no enabled active modules")

        missing_for_professional = conn.execute(text("""
            SELECT m.code
            FROM system_modules m
            WHERE m.is_active = true
              AND NOT EXISTS (
                  SELECT 1
                  FROM plan_modules pm
                  JOIN subscription_plans p ON p.id = pm.plan_id
                  WHERE p.code = 'professional' AND pm.module_id = m.id AND pm.is_enabled = true
              )
        """)).scalars().all()
        if missing_for_professional:
            fail(f"professional plan is missing active modules: {sorted(missing_for_professional)}")

    engine.dispose()


def main() -> int:
    audit_static_contract()
    audit_database_contract()
    print("Module entitlement contract audit passed: identity, technical catalog, guards, plans and DB relationships are consistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
