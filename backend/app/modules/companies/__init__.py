__all__ = ["Company", "UserCompanyAccess"]


def __getattr__(name: str):
    if name == "Company":
        from .models import Company
        return Company
    if name == "UserCompanyAccess":
        from .user_access import UserCompanyAccess
        return UserCompanyAccess
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
