"""CI gate for the PrimeERP modular architecture."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.module_engine import (  # noqa: E402
    DEFAULT_MODULE_PACKAGE,
    bootstrap_module_registry,
    validate_catalog_dependencies,
)


def main() -> int:
    validate_catalog_dependencies()
    registry = bootstrap_module_registry()
    modules = registry.all()
    if not modules:
        raise RuntimeError("No installable PrimeERP modules were discovered")

    keys = [module.key for module in modules]
    if len(keys) != len(set(keys)):
        raise RuntimeError("Duplicate module technical names discovered")

    print(f"Module architecture check passed: {len(modules)} add-ons discovered from {DEFAULT_MODULE_PACKAGE}")
    for module in modules:
        deps = ", ".join(module.dependencies) or "-"
        print(f"- {module.key} v{module.version} | deps: {deps}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
