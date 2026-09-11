from app.modules.integrations.salla_service import _is_stale, _version_key


def test_numeric_versions_are_ordered_numerically():
    assert _version_key("10") > _version_key("9")
    assert _is_stale("10", "9") is True
    assert _is_stale("9", "10") is False


def test_equal_versions_are_stale():
    assert _is_stale("2026-09-11T10:00:00", "2026-09-11T10:00:00") is True


def test_missing_versions_do_not_block_event_processing():
    assert _is_stale(None, "10") is False
    assert _is_stale("10", None) is False


def test_text_versions_are_stable_and_ordered():
    assert _is_stale("v2", "v1") is True
    assert _is_stale("v1", "v2") is False
