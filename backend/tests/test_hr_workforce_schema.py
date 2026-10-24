import pytest
from pydantic import ValidationError

from app.modules.hr.router import WorkforceUpdate


def test_workforce_update_accepts_supported_profile_fields():
    payload = WorkforceUpdate(
        full_name="Test Employee",
        phone="+201000000000",
        address="Test address",
        preferred_language="ar",
    )
    assert payload.full_name == "Test Employee"
    assert payload.preferred_language == "ar"


def test_workforce_update_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        WorkforceUpdate(full_name="Test Employee", is_superuser=True)


@pytest.mark.parametrize("language", ["fr", "xx", ""])
def test_workforce_update_rejects_unsupported_language(language):
    with pytest.raises(ValidationError):
        WorkforceUpdate(preferred_language=language)


def test_workforce_update_rejects_oversized_profile_values():
    with pytest.raises(ValidationError):
        WorkforceUpdate(phone="1" * 31)
    with pytest.raises(ValidationError):
        WorkforceUpdate(address="x" * 1001)
