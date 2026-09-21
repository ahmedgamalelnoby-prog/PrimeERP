from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_dashboard_api_is_tenant_scoped_and_uses_live_financial_data():
    router = (ROOT / "modules/platform/dashboard_router.py").read_text(encoding="utf-8")
    assert '"/summary"' in router
    assert "current_user.tenant_id" in router
    assert "SalesDocument.document_type == \"invoice\"" in router
    assert "SalesDocument.status == \"posted\"" in router


def test_dashboard_is_registered_in_v1_router():
    router = (ROOT / "api/v1/router.py").read_text(encoding="utf-8")
    assert "dashboard_router" in router
    assert 'prefix="/platform/dashboard"' in (ROOT / "modules/platform/api/router.py").read_text(encoding="utf-8")


def test_dashboard_frontend_consumes_the_live_summary_contract():
    api = (ROOT.parent / "frontend/src/modules/platform/api/dashboard.api.ts").read_text(encoding="utf-8")
    page = (ROOT.parent / "frontend/src/modules/platform/pages/DashboardPage.tsx").read_text(encoding="utf-8")
    assert "dashboardApi.summary()" in page
    assert "/platform/dashboard/summary" in api
    assert "current_month_revenue" in api
    assert "previous_month_revenue" in api
