from app.modules.egyptian_einvoice.crud import _terminal_status_cannot_regress


def test_eta_terminal_status_cannot_regress():
    for terminal in ("valid", "rejected", "cancelled"):
        assert _terminal_status_cannot_regress(terminal, "submitted") is True
        assert _terminal_status_cannot_regress(terminal, terminal) is False


def test_eta_non_terminal_status_can_progress():
    for current in ("draft", "queued", "submitted", "error"):
        assert _terminal_status_cannot_regress(current, "valid") is False
