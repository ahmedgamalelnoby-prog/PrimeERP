from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CHECKS = (
    ("modular architecture", "check_modular_architecture.py"),
    ("API security", "check_api_security.py"),
    ("production config", "check_production_config.py"),
    ("release readiness", "check_release_readiness.py"),
    ("Alembic graph", "check_alembic_graph.py"),
    ("product architecture", "check_product_architecture.py"),
    ("frontend/backend alignment", "check_frontend_backend_alignment.py"),
)


def main() -> int:
    failures: list[tuple[str, int]] = []
    print("PrimeERP architecture audit: running all static gates before failing.")
    for label, script in CHECKS:
        print(f"\n===== {label}: {script} =====", flush=True)
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / script)],
            cwd=ROOT,
            check=False,
        )
        if completed.returncode != 0:
            failures.append((label, completed.returncode))
            print(f"===== {label}: FAILED ({completed.returncode}) =====", flush=True)
        else:
            print(f"===== {label}: PASSED =====", flush=True)

    if failures:
        print("\nARCHITECTURE AUDIT SUMMARY: FAIL")
        for label, code in failures:
            print(f"- {label}: exit code {code}")
        return 1

    print("\nARCHITECTURE AUDIT SUMMARY: PASS — all static gates passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
