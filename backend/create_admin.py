"""Backward-compatible entry point for the supported Super Admin bootstrapper.

The old script created a legacy User shape and contained a hard-coded weak
password. Keep the entry point for existing operational habits, but delegate
to the single supported bootstrap implementation and require a secure
password through PRIMEERP_SUPERADMIN_PASSWORD or an interactive prompt.
"""

from scripts.create_super_admin import main


if __name__ == "__main__":
    main()
