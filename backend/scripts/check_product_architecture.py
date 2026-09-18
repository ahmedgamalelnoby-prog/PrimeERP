from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.config import settings
from app.modules.platform.module_registry import MODULE_REGISTRY



def main() -> None:
    keys = [str(item["key"]) for item in MODULE_REGISTRY]
    if len(keys) < 50:
        raise SystemExit(f"Module registry coverage is unexpectedly low: {len(keys)}")
    if len(keys) != len(set(keys)):
        raise SystemExit("Module registry contains duplicate keys")
    if not settings.AI_MODEL:
        raise SystemExit("AI_MODEL must be configured")
    if not settings.AI_KNOWLEDGE_VERSION:
        raise SystemExit("AI_KNOWLEDGE_VERSION must be configured")

    forbidden = ("company_id = 1", "companyId = 1", "company_id=1", "companyId=1")
    scan_roots = (ROOT / "backend" / "app", ROOT / "frontend" / "src")
    hits: list[str] = []
    for scan_root in scan_roots:
        for path in scan_root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx"}:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for token in forbidden:
                if token in text:
                    hits.append(f"{path.relative_to(ROOT)} contains {token!r}")
    if hits:
        raise SystemExit("Hard-coded company fallback detected:\n" + "\n".join(hits))

    helpdesk = (ROOT / "backend" / "app" / "modules" / "helpdesk_ai" / "router.py").read_text(encoding="utf-8")
    if "/ai/advice" not in helpdesk or "knowledge_context" not in helpdesk:
        raise SystemExit("AI advisory is not grounded in the live module registry")

    print(f"Product architecture audit: PASS ({len(keys)} registered modules; AI knowledge {settings.AI_KNOWLEDGE_VERSION})")


if __name__ == "__main__":
    main()
