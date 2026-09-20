from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend" / "src"
BACKEND = ROOT / "backend" / "app"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def normalize_contract(text: str) -> str:
    return re.sub(r"\s+", "", text)


def main() -> None:
    main_file = read(FRONTEND / "app" / "main.tsx")
    if "@/shared/api/interceptors" not in main_file:
        raise SystemExit("Frontend API authentication interceptor is not initialized globally")

    ts_files = list(FRONTEND.rglob("*.ts")) + list(FRONTEND.rglob("*.tsx"))
    forbidden_patterns = (
        r"\bfetch\s*\(",
        r"\bAPI_BASE\s*=",
        r'useState\(\s*["\']1["\']\s*\)',
        r"company[_A-Za-z]*\s*[:=]\s*1\b",
    )
    violations: list[str] = []
    for path in ts_files:
        text = read(path)
        if path.name in {"client.ts", "env.ts"}:
            continue
        for pattern in forbidden_patterns:
            if re.search(pattern, text):
                violations.append(f"{path.relative_to(ROOT)} matches {pattern}")
    if violations:
        raise SystemExit("Frontend integration violations:\n" + "\n".join(violations))

    router = read(FRONTEND / "app" / "router" / "AppRouter.tsx")
    navigation = read(FRONTEND / "app" / "navigation.ts")
    nav_paths = sorted(set(re.findall(r'path:\s*"([^"]+)"', navigation)))
    missing_routes = [
        path
        for path in nav_paths
        if f'path="{path}"' not in router and f'path="/{path.lstrip("/")}"' not in router
    ]
    if missing_routes:
        raise SystemExit("Navigation paths missing from AppRouter:\n" + "\n".join(missing_routes))

    import_paths = re.findall(r'from ["\'](@/[^"\']+)["\']', router)
    missing_imports: list[str] = []
    for spec in import_paths:
        rel = spec[2:]
        candidates = [
            FRONTEND / f"{rel}.ts",
            FRONTEND / f"{rel}.tsx",
            FRONTEND / rel / "index.ts",
            FRONTEND / rel / "index.tsx",
        ]
        if not any(candidate.exists() for candidate in candidates):
            missing_imports.append(spec)
    if missing_imports:
        raise SystemExit("AppRouter imports missing frontend modules:\n" + "\n".join(missing_imports))

    required_contracts = {
        "/platform/modules": BACKEND / "modules" / "platform" / "api" / "router.py",
        "/helpdesk/ai/answer": BACKEND / "modules" / "helpdesk_ai" / "router.py",
        "/helpdesk/ai/advice": BACKEND / "modules" / "helpdesk_ai" / "router.py",
        "/reports/ai/analyze": BACKEND / "modules" / "reports" / "router.py",
        "/reports/deliver": BACKEND / "modules" / "reports" / "router.py",
        "/reports/schedules": BACKEND / "modules" / "reports" / "router.py",
        "/treasury/cheques": BACKEND / "modules" / "treasury" / "router.py",
        "/commerce/payments": BACKEND / "modules" / "commerce" / "router.py",
        "/inventory/stock-moves": BACKEND / "modules" / "inventory" / "stock_moves" / "router.py",
        "/inventory/transfers": BACKEND / "modules" / "inventory" / "transfers" / "router.py",
        "/chart-of-accounts/combinations": BACKEND / "modules" / "accounting" / "chart_of_accounts" / "router.py",
        "/accounting/journal-entries/journals": BACKEND / "modules" / "accounting" / "journals" / "api" / "journal_entries.py",
        "/accounting/reports/summary": BACKEND / "modules" / "accounting" / "reports" / "router.py",
        "/roles/permissions": BACKEND / "modules" / "roles" / "router.py",
        "/identity/users": BACKEND / "modules" / "identity" / "api" / "users.py",
        "/plans/": BACKEND / "modules" / "platform" / "plans" / "router.py",
    }
    backend_fragments: dict[str, tuple[str, ...]] = {
        "/platform/modules": ('router = APIRouter(prefix="/platform/modules"',),
        "/helpdesk/ai/answer": ('@router.post("/ai/answer"',),
        "/helpdesk/ai/advice": ('@router.post("/ai/advice"',),
        "/reports/ai/analyze": ('router = APIRouter(prefix="/reports"', '@router.post("/ai/analyze"'),
        "/reports/deliver": ('router = APIRouter(prefix="/reports"', '@router.post("/deliver"'),
        "/reports/schedules": ('router = APIRouter(prefix="/reports"', '@router.post("/schedules"'),
        "/treasury/cheques": ('router = APIRouter(prefix="/treasury"', '@router.post("/cheques"'),
        "/commerce/payments": ('router = APIRouter(prefix="/commerce"', '@router.get("/payments"'),
        "/inventory/stock-moves": ('router = APIRouter(prefix="/inventory/stock-moves"',),
        "/inventory/transfers": ('prefix="/inventory/transfers"',),
        "/chart-of-accounts/combinations": ('router = APIRouter(prefix="/chart-of-accounts"', '@router.get("/combinations"'),
        "/accounting/journal-entries/journals": ('@router.get("/journals"',),
        "/accounting/reports/summary": ('prefix="/accounting/reports"', '@router.get("/summary"'),
        "/roles/permissions": ('router = APIRouter(prefix="/roles"', '@router.get("/permissions"'),
        "/identity/users": ('prefix="/users"',),
        "/plans/": ('prefix="/plans"', '@router.get(', '"/"'),
    }
    for contract, backend_file in required_contracts.items():
        if not backend_file.exists():
            raise SystemExit(f"Backend contract file missing for {contract}: {backend_file}")
        backend_text = normalize_contract(read(backend_file))
        fragments = backend_fragments.get(contract, (contract,))
        normalized_fragments = [normalize_contract(fragment) for fragment in fragments]
        if not all(fragment in backend_text for fragment in normalized_fragments):
            raise SystemExit(f"Backend contract not found: {contract} in {backend_file.relative_to(ROOT)}")

    roles_api = read(FRONTEND / "modules" / "roles" / "api" / "roles.api.ts")
    normalized_roles_api = normalize_contract(roles_api)
    if "/roles/permissions" not in normalized_roles_api and "BASE_URL}/permissions" not in roles_api:
        raise SystemExit("Roles frontend is not aligned with the backend /roles contract")


    # Every backend module must have a discoverable frontend module, and every
    # frontend module must map to a backend namespace unless explicitly marked
    # as shell/public-only. This prevents silent UI/backend drift.
    backend_modules = {
        path.name for path in (BACKEND / "modules").iterdir()
        if path.is_dir() and path.name != "ADDON_TEMPLATE" and path.name != "__pycache__"
    }
    frontend_modules = {
        path.name for path in (FRONTEND / "modules").iterdir()
        if path.is_dir()
    }
    aliases = {"egyptian_einvoice": "egyptian-einvoice", "ai_reporting": "ai-reporting", "catalog": "products", "helpdesk_ai": "helpdesk", "uom": "products", "approvals": "operations", "workflow": "operations", "customers": "commerce"}
    backend_frontend_names = {
        aliases.get(name, name) for name in backend_modules
    }
    frontend_only_allowed = {
        "assets", "checks", "cost-centers", "expenses", "hotels", "insurance",
        "language", "permissions", "real-estate", "reservations",
        "restaurant", "saas", "suppliers", "time-tracking", "users",
        "work-orders", "public",
    }
    backend_only_allowed = {
        "organization", "jurisdiction", "notifications", "operations",
        "dashboard", "integrations",
        # Cross-cutting backend services consumed by domain modules; they do not
        # represent standalone user-facing navigation modules.
        "ai_reporting", "completion", "core_integration",
    }
    missing_frontend = sorted(
        name for name in backend_frontend_names
        if name not in frontend_modules and name not in backend_only_allowed
    )
    frontend_to_backend = {
        "ai-reporting": "ai_reporting",
        "egyptian-einvoice": "egyptian_einvoice",
        "products": "catalog",
        "helpdesk": "helpdesk_ai",
        "operations": "operations",
        "commerce": "commerce",
        "approvals": "operations",
        "workflow": "operations",
        "customers": "commerce",
    }
    frontend_backend_names = {frontend_to_backend.get(name, name) for name in frontend_modules}
    missing_backend = sorted(
        name for name in frontend_backend_names
        if name not in backend_modules and name not in frontend_only_allowed
    )
    if missing_frontend:
        raise SystemExit(
            "Backend modules missing frontend modules:\n" + "\n".join(missing_frontend)
        )
    if missing_backend:
        raise SystemExit(
            "Frontend modules missing backend modules:\n" + "\n".join(missing_backend)
        )

    print(f"Frontend/backend alignment audit: PASS ({len(nav_paths)} navigation paths; {len(required_contracts)} critical API contracts)")


if __name__ == "__main__":
    main()
