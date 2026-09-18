from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend" / "src"
BACKEND = ROOT / "backend" / "app"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


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
    backend_fragments = {
        "/accounting/journal-entries/journals": '@router.get("/journals"',
        "/identity/users": 'prefix="/users"',
    }
    for contract, backend_file in required_contracts.items():
        if not backend_file.exists():
            raise SystemExit(f"Backend contract file missing for {contract}: {backend_file}")
        fragment = backend_fragments.get(contract, contract)
        if fragment not in read(backend_file):
            raise SystemExit(f"Backend contract not found: {contract} in {backend_file.relative_to(ROOT)}")

    if "/roles/permissions" not in read(FRONTEND / "modules" / "roles" / "api" / "roles.api.ts"):
        raise SystemExit("Roles frontend is not aligned with the backend /roles contract")

    print(f"Frontend/backend alignment audit: PASS ({len(nav_paths)} navigation paths; {len(required_contracts)} critical API contracts)")


if __name__ == "__main__":
    main()
