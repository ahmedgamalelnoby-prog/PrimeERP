"""Template for a PrimeERP installable add-on.

Copy this package into the appropriate domain and replace the placeholder values.
"""

from app.core.module_engine.manifest import manifest

MANIFEST = manifest(
    technical_name="domain/addon_name",
    display_name="Add-on Name",
    version="1.0.0",
    domain="domain",
    dependencies=(),
    optional_dependencies=(),
    permissions=frozenset(),
    routes=(),
    menus=(),
    installable=False,
    tenant_enabled=True,
)
