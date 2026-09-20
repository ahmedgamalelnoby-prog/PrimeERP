from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT_LOG = ROOT / "architecture-audit.log"

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
    log_parts: list[str] = [
        "PrimeERP architecture audit",
        f"Python: {sys.executable}",
        f"Root: {ROOT}",
    ]

    print("PrimeERP architecture audit: running all static gates before failing.", flush=True)
    for label, script in CHECKS:
        header = f"===== {label}: {script} ====="
        print(f"\n{header}", flush=True)
        try:
            completed = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / script)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except Exception as exc:
            failures.append((label, 1))
            detail = f"{type(exc).__name__}: {exc}"
            print(f"{header}\n{detail}", flush=True)
            log_parts.extend([header, detail])
            continue

        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        if stdout:
            print(stdout, end="" if stdout.endswith("\n") else "\n", flush=True)
        if stderr:
            print(stderr, end="" if stderr.endswith("\n") else "\n", file=sys.stderr, flush=True)

        log_parts.extend([header, f"exit_code={completed.returncode}", "[stdout]", stdout, "[stderr]", stderr])

        if completed.returncode != 0:
            failures.append((label, completed.returncode))
            print(f"===== {label}: FAILED ({completed.returncode}) =====", flush=True)
        else:
            print(f"===== {label}: PASSED =====", flush=True)

    try:
        AUDIT_LOG.write_text("\n\n".join(log_parts) + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"WARNING: could not persist architecture audit log: {exc}", flush=True)

    if failures:
        print("\nARCHITECTURE AUDIT SUMMARY: FAIL", flush=True)
        for label, code in failures:
            print(f"- {label}: exit code {code}", flush=True)
        return 1

    print("\nARCHITECTURE AUDIT SUMMARY: PASS — all static gates passed.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
