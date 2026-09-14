import os

from app.modules.ai_reporting.service import AIAnalysisService, rows_to_csv


def test_rows_to_csv_is_excel_safe_utf8():
    payload = rows_to_csv([{"name": "عميل", "amount": 1250}, {"name": "A", "amount": 50}])
    assert payload.startswith(b"\xef\xbb\xbf")
    assert "عميل" in payload.decode("utf-8-sig")
    assert "1250" in payload.decode("utf-8-sig")


def test_ai_analysis_has_safe_disabled_mode(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = AIAnalysisService().analyze("Sales", {"revenue": 100})
    assert result["provider"] == "disabled"
    assert "OPENAI_API_KEY" in result["summary"]
