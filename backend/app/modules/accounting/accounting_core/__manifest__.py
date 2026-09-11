"""Manifest for the Accounting Core add-on."""

from app.core.module_engine.manifest import manifest


MANIFEST = manifest(
    technical_name="accounting/accounting_core",
    display_name="Accounting Core",
    version="1.0.0",
    domain="accounting",
    metadata={
        "migration_status": "foundation",
        "legacy_path": "app.modules.accounting",
    },
)
